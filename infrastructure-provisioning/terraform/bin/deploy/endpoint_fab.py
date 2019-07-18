from fabric import *
from patchwork.files import exists
import logging
import argparse
import sys
import traceback
import random
import string

conn = None
args = None
keystore_passwd = None
java_home = None


def create_user():
    initial_user = 'ubuntu'
    sudo_group = 'sudo'
    with Connection(host=args.hostname, user=initial_user,
                    connect_kwargs={'key_filename': args.keyfile}) as conn:
        try:
            if not exists(conn,
                          '/home/{}/.ssh_user_ensured'.format(initial_user)):
                conn.sudo('useradd -m -G {1} -s /bin/bash {0}'
                          .format(args.os_user, sudo_group))
                conn.sudo(
                    'bash -c \'echo "{} ALL = NOPASSWD:ALL" >> /etc/sudoers\''
                        .format(args.os_user, initial_user))
                conn.sudo('mkdir /home/{}/.ssh'.format(args.os_user))
                conn.sudo('chown -R {0}:{0} /home/{1}/.ssh/'
                          .format(initial_user, args.os_user))
                conn.sudo('cat /home/{0}/.ssh/authorized_keys > '
                          '/home/{1}/.ssh/authorized_keys'
                          .format(initial_user, args.os_user))
                conn.sudo(
                    'chown -R {0}:{0} /home/{0}/.ssh/'.format(args.os_user))
                conn.sudo('chmod 700 /home/{0}/.ssh'.format(args.os_user))
                conn.sudo('chmod 600 /home/{0}/.ssh/authorized_keys'
                          .format(args.os_user))
                conn.sudo(
                    'touch /home/{}/.ssh_user_ensured'.format(initial_user))
        except Exception as err:
            logging.error('Failed to create new os_user: ', str(err))
            sys.exit(1)


def copy_keys():
    try:
        conn.put(args.keyfile, ' /home/{}/keys'.format(args.os_user))
    except Exception as err:
        logging.error('Failed to copy keys ', str(err))
        traceback.print_exc()
        sys.exit(1)


def ensure_crutch_endpoint():
    try:
        if not exists(conn, '/home/{}/.ensure_dir'.format(args.os_user)):
            conn.sudo('mkdir /home/{}/.ensure_dir'.format(args.os_user))
    except Exception as err:
        logging.error('Failed to create ~/.ensure_dir/: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def ensure_logs_endpoint():
    log_root_dir = "/var/opt/dlab/log"
    supervisor_log_file = "/var/log/application/provision-service.log"
    if not exists(conn, args.dlab_path):
        conn.sudo("mkdir -p {}".format(args.dlab_path))
        conn.sudo("chown -R {} {}".format(args.os_user, args.dlab_path))
    if not exists(conn, log_root_dir):
        conn.sudo('mkdir -p {}/provisioning'.format(log_root_dir))
        conn.sudo('touch {}/provisioning/provisioning.log'.format(log_root_dir))
        conn.sudo('chmod 666 {}/provisioning/provisioning.log'
                  .format(log_root_dir))
    if not exists(conn, supervisor_log_file):
        conn.sudo("mkdir -p /var/log/application")
        conn.sudo("touch {}".format(supervisor_log_file))
        conn.sudo("chmod 666 {}".format(supervisor_log_file))


def ensure_jre_jdk_endpoint():
    try:
        if not exists(conn, '/home/{}/.ensure_dir/jre_jdk_ensured'
                .format(args.os_user)):
            conn.sudo('apt-get install -y openjdk-8-jre-headless')
            conn.sudo('apt-get install -y openjdk-8-jdk-headless')
            conn.sudo('touch /home/{}/.ensure_dir/jre_jdk_ensured'
                      .format(args.os_user))
    except Exception as err:
        logging.error('Failed to install Java JDK: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def ensure_supervisor_endpoint():
    try:
        if not exists(conn, '/home/{}/.ensure_dir/superv_ensured'
                .format(args.os_user)):
            conn.sudo('apt-get -y install supervisor')
            conn.sudo('update-rc.d supervisor defaults')
            conn.sudo('update-rc.d supervisor enable')
            conn.sudo('touch /home/{}/.ensure_dir/superv_ensured'
                      .format(args.os_user))
    except Exception as err:
        logging.error('Failed to install Supervisor: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def ensure_docker_endpoint():
    try:
        if not exists(conn, '/home/{}/.ensure_dir/docker_ensured'
                .format(args.os_user)):
            conn.sudo("bash -c "
                      "'curl -fsSL https://download.docker.com/linux/ubuntu/gpg"
                      " | apt-key add -'")
            conn.sudo('add-apt-repository "deb [arch=amd64] '
                      'https://download.docker.com/linux/ubuntu '
                      '$(lsb_release -cs) stable"')
            conn.sudo('apt-get update')
            conn.sudo('apt-cache policy docker-ce')
            conn.sudo('apt-get install -y docker-ce={}'
                      .format(args.docker_version))
            dns_ip_resolve = (conn.run("systemd-resolve --status "
                                       "| grep -A 5 'Current Scopes: DNS' "
                                       "| grep 'DNS Servers:' "
                                       "| awk '{print $3}'")
                              .stdout.rstrip("\n\r"))
            if not exists(conn, '{}/tmp'.format(args.dlab_path)):
                conn.run('mkdir -p {}/tmp'.format(args.dlab_path))
            conn.put('./daemon.json',
                     '{}/tmp/daemon.json'.format(args.dlab_path))
            conn.sudo('sed -i "s|REPOSITORY|{}:{}|g" {}/tmp/daemon.json'
                      .format(args.repository_address,
                              args.repository_port,
                              args.dlab_path))
            conn.sudo('sed -i "s|DNS_IP_RESOLVE|{}|g" {}/tmp/daemon.json'
                      .format(dns_ip_resolve, args.dlab_path))
            conn.sudo('mv {}/tmp/daemon.json /etc/docker'
                      .format(args.dlab_path))
            conn.sudo('usermod -a -G docker ' + args.os_user)
            conn.sudo('update-rc.d docker defaults')
            conn.sudo('update-rc.d docker enable')
            conn.sudo('service docker restart')
            conn.sudo('touch /home/{}/.ensure_dir/docker_ensured'
                      .format(args.os_user))
    except Exception as err:
        logging.error('Failed to install Docker: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def create_key_dir_endpoint():
    try:
        if not exists(conn, '/home/{}/keys'.format(args.os_user)):
            conn.run('mkdir /home/{}/keys'.format(args.os_user))
    except Exception as err:
        logging.error('Failed create keys directory as ~/keys: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def generate_passwd(size=10,
                    chars=string.digits + string.ascii_letters):
    global keystore_passwd
    keystore_passwd = ''.join(random.choice(chars) for _ in range(size))


def configure_keystore_endpoint(os_user):
    try:
        if not exists(conn,
                      '/home/{}/keys/dlab.keystore.jks'.format(args.os_user)):
            conn.sudo('keytool -genkeypair -alias dlab -keyalg RSA '
                      '-validity 730 -storepass {1} -keypass {1} '
                      '-keystore /home/{0}/keys/dlab.keystore.jks  '
                      '-keysize 2048 -dname "CN={2}"'
                      .format(os_user, keystore_passwd, args.hostname))
        if not exists(conn, '/home/{}/keys/dlab.crt'.format(args.os_user)):
            conn.sudo('keytool -exportcert -alias dlab -storepass {1} '
                      '-file /home/{0}/keys/dlab.crt '
                      '-keystore /home/{0}/keys/dlab.keystore.jks'
                      .format(os_user, keystore_passwd))
        if not exists(conn,
                      '/home/{}/.ensure_dir/cert_imported'
                              .format(args.os_user)):
            conn.sudo('keytool -importcert -trustcacerts -alias dlab '
                      '-file /home/{0}/keys/dlab.crt -noprompt  '
                      '-storepass changeit -keystore {1}/lib/security/cacerts'
                      .format(os_user, java_home))
            conn.sudo('touch /home/{}/.ensure_dir/cert_imported'
                      .format(args.os_user))
    except Exception as err:
        logging.error('Failed to configure Keystore certificates: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def configure_supervisor_endpoint():
    try:
        if not exists(conn,
                      '/home/{}/.ensure_dir/configure_supervisor_ensured'
                              .format(args.os_user)):
            supervisor_conf = '/etc/supervisor/conf.d/supervisor_svc.conf'
            if not exists(conn, '{}/tmp'.format(args.dlab_path)):
                conn.run('mkdir -p {}/tmp'.format(args.dlab_path))
            conn.put('./supervisor_svc.conf',
                     '{}/tmp/supervisor_svc.conf'.format(args.dlab_path))
            dlab_conf_dir = '{}/conf/'.format(args.dlab_path)
            if not exists(conn, dlab_conf_dir):
                conn.run('mkdir -p {}'.format(dlab_conf_dir))
            web_path = '{}/webapp'.format(args.dlab_path)
            if not exists(conn, web_path):
                conn.run('mkdir -p {}'.format(web_path))
            conn.sudo('sed -i "s|OS_USR|{}|g" {}/tmp/supervisor_svc.conf'
                      .format(args.os_user, args.dlab_path))
            conn.sudo('sed -i "s|WEB_CONF|{}|g" {}/tmp/supervisor_svc.conf'
                      .format(dlab_conf_dir, args.dlab_path))
            conn.sudo('sed -i \'s=WEB_APP_DIR={}=\' {}/tmp/supervisor_svc.conf'
                      .format(web_path, args.dlab_path))
            conn.sudo('cp {}/tmp/supervisor_svc.conf {}'
                      .format(args.dlab_path, supervisor_conf))
            conn.put('./provisioning.yml', '{}provisioning.yml'
                     .format(dlab_conf_dir))
            conn.sudo('sed -i "s|KEYNAME|{}|g" {}provisioning.yml'
                      .format(args.conf_key_name, dlab_conf_dir))
            conn.sudo('sed -i "s|KEYSTORE_PASSWORD|{}|g" {}provisioning.yml'
                      .format(keystore_passwd, dlab_conf_dir))
            conn.sudo('sed -i "s|JRE_HOME|{}|g" {}provisioning.yml'
                      .format(java_home, dlab_conf_dir))
            conn.sudo('sed -i "s|CLOUD_PROVIDER|{}|g" {}provisioning.yml'
                      .format(args.cloud_provider, dlab_conf_dir))
            conn.sudo('sed -i "s|SSN_HOST|{}|g" {}provisioning.yml'
                      .format(args.ssn_host, dlab_conf_dir))
            conn.sudo('sed -i "s|MONGO_PASSWORD|{}|g" {}provisioning.yml'
                      .format(args.mongo_password, dlab_conf_dir))
            conn.sudo('touch /home/{}/.ensure_dir/configure_supervisor_ensured'
                      .format(args.os_user))
    except Exception as err:
        logging.error('Failed to configure Supervisor: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def ensure_jar_endpoint():
    try:
        ensure_file = ('/home/{}/.ensure_dir/backend_jar_ensured'
                       .format(args.os_user))
        if not exists(conn, ensure_file):
            web_path = '{}/webapp'.format(args.dlab_path)
            if not exists(conn, web_path):
                conn.run('mkdir -p {}'.format(web_path))

            conn.run('wget -P {}  --user={} --password={} '
                     'https://{}/repository/packages/provisioning-service-'
                     '2.1.jar --no-check-certificate'
                     .format(web_path, args.repository_user,
                             args.repository_pass, args.repository_address))
            conn.run('mv {0}/*.jar {0}/provisioning-service.jar'
                     .format(web_path))
            conn.sudo('touch {}'.format(ensure_file))
    except Exception as err:
        logging.error('Failed to download jar-provisioner: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def start_supervisor_endpoint():
    try:
        conn.sudo("service supervisor restart")
    except Exception as err:
        logging.error('Unable to start Supervisor: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def pull_docker_images():
    try:
        ensure_file = ('/home/{}/.ensure_dir/docker_images_pulled'
                       .format(args.os_user))
        if not exists(conn, ensure_file):
            conn.sudo('docker login -u {} -p {} {}:{}'
                      .format(args.repository_user,
                              args.repository_pass,
                              args.repository_address,
                              args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-base'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-edge'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-jupyter'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-rstudio'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-zeppelin'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-tensor'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-tensor-rstudio'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-deeplearning'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-dataengine-service'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker pull {}:{}/docker.dlab-dataengine'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-base docker.dlab-base'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-edge docker.dlab-edge'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-jupyter docker.dlab-jupyter'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-rstudio docker.dlab-rstudio'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-zeppelin '
                      'docker.dlab-zeppelin'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-tensor docker.dlab-tensor'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-tensor-rstudio '
                      'docker.dlab-tensor-rstudio'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-deeplearning '
                      'docker.dlab-deeplearning'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-dataengine-service '
                      'docker.dlab-dataengine-service'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker tag {}:{}/docker.dlab-dataengine '
                      'docker.dlab-dataengine'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-base'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-edge'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-jupyter'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-rstudio'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-zeppelin'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-tensor'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-tensor-rstudio'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-deeplearning'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-dataengine-service'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('docker rmi {}:{}/docker.dlab-dataengine'
                      .format(args.repository_address, args.repository_port))
            conn.sudo('chown -R {0}:docker /home/{0}/.docker/'
                      .format(args.os_user))
            conn.sudo('touch {}'.format(ensure_file))
    except Exception as err:
        logging.error('Failed to pull Docker images: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def init_args():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--dlab_path', type=str, default='')
    parser.add_argument('--key_name', type=str, default='')
    parser.add_argument('--conf_key_name', type=str, default='')
    parser.add_argument('--keyfile', type=str, default='')
    parser.add_argument('--hostname', type=str, default='')
    parser.add_argument('--os_user', type=str, default='dlab-user')
    parser.add_argument('--cloud_provider', type=str, default='')
    parser.add_argument('--ssn_host', type=str, default='')
    parser.add_argument('--mongo_password', type=str, default='')
    parser.add_argument('--repository_address', type=str, default='')
    parser.add_argument('--repository_port', type=str, default='')
    parser.add_argument('--repository_user', type=str, default='')
    parser.add_argument('--repository_pass', type=str, default='')
    parser.add_argument('--docker_version', type=str,
                        default='18.06.3~ce~3-0~ubuntu')
    args = parser.parse_known_args()


def update_system():
    conn.sudo('apt-get update')


def init_dlab_connection(ip=None, user=None,
                         pkey=None):
    global conn
    if not ip:
        ip = args.hostname
    if not user:
        user = args.os_user
    if not pkey:
        pkey = args.keyfile
    try:
        conn = Connection(ip, user, connect_kwargs={'key_filename': pkey})
    except Exception as err:
        logging.error('Failed connect as dlab-user: ', str(err))
        traceback.print_exc()
        sys.exit(1)


def set_java_home():
    global java_home
    command = ('bash -c "update-alternatives --query java | grep \'Value: \' '
               '| grep -o \'/.*/jre\'" ')
    java_home = (conn.sudo(command).stdout.rstrip("\n\r"))


def close_connection():
    global conn
    conn.close()


def start_deploy():
    init_args()

    logging.info("Creating dlab-user")
    create_user()

    init_dlab_connection()
    update_system()
    generate_passwd()

    logging.info("Configuring Crutch")
    ensure_crutch_endpoint()

    logging.info("Configuring Logs")
    ensure_logs_endpoint()

    logging.info("Installing Java")
    ensure_jre_jdk_endpoint()

    set_java_home()

    logging.info("Installing Supervisor")
    ensure_supervisor_endpoint()

    logging.info("Installing Docker")
    ensure_docker_endpoint()

    logging.info("Configuring Supervisor")
    configure_supervisor_endpoint()

    logging.info("Creating key directory")
    create_key_dir_endpoint()

    logging.info("Starting Endpoint")
    configure_keystore_endpoint(args.os_user)

    logging.info("Ensure jar")
    ensure_jar_endpoint()

    logging.info("Starting supervisor")
    start_supervisor_endpoint()

    logging.info("Pulling docker images")
    pull_docker_images()

    close_connection()


if __name__ == "__main__":
    start_deploy()

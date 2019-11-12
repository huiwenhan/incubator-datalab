# *****************************************************************************
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# ******************************************************************************

variable "namespace_name" {
    default = "dlab"
}

variable "credentials_file_path" {
  default = ""
}

variable "project_id" {
  default = ""
}

variable "region" {
  default = "us-west1"
}

variable "zone" {
  default = "a"
}

variable "vpc_name" {
  default = ""
}

variable "subnet_name" {
  default = ""
}

variable "service_base_name" {
  default = "dlab-k8s"
}

variable "subnet_cidr" {
  default = "172.31.0.0/24"
}

variable "additional_tag" {
  default = "product:dlab"
}

variable "ssn_k8s_workers_count" {
  default = 1
}

variable "gke_cluster_version" {
  default = "1.13.11-gke.9"
}

// Couldn't assign in GCP
//variable "tag_resource_id" {
//  default = "user:tag"
//}

variable "ssn_k8s_workers_shape" {
  default = "n1-standard-1"
}

variable "service_account_iam_roles" {
  default = [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/storage.objectViewer",
    "roles/iam.serviceAccountTokenCreator",
  ]
}

variable "k8s_gke_endpoint" {
    default = ""
}

variable "k8s_gke_client_access_token" {
    default = ""
}

variable "k8s_gke_clinet_cert" {
    default = ""
}

variable "k8s_gke_client_key" {
    default = ""
}

variable "k8s_gke_cluster_ca" {
    default = ""
}

variable "ssn_k8s_alb_dns_name" {
    default = ""
}

variable "keycloak_user" {
    default = "dlab-admin"
}

variable "mysql_user" {
    default = "keycloak"
}

variable "mysql_db_name" {
    default = "keycloak"
}

variable "ldap_usernameAttr" {
    default = "uid"
}

variable "ldap_rdnAttr" {
    default = "uid"
}

variable "ldap_uuidAttr" {
    default = "uid"
}

variable "ldap_users_group" {
    default = "ou=People"
}

variable "ldap_dn" {
    default = "dc=example,dc=com"
}

variable "ldap_user" {
    default = "cn=admin"
}

variable "ldap_bind_creds" {
    default = ""
}

variable "ldap_host" {
    default = ""
}

variable "mongo_db_username" {
    default = "admin"
}

variable "mongo_dbname" {
    default = "dlabdb"
}

variable "mongo_image_tag" {
    default = "4.0.10-debian-9-r13"
    description = "MongoDB Image tag"
}

variable "mongo_service_port" {
    default = "27017"
}

variable "mongo_node_port" {
    default = "31017"
}

variable "mongo_service_name" {
    default = "mongo-ha-mongodb"
}

# variable "endpoint_eip_address" {}

variable "env_os" {
  default = "debian"
}

variable "ssn_keystore_password" {
  default = ""
}

variable "endpoint_keystore_password" {
  default = ""
}

variable "big_query_dataset" {
  default = ""
}

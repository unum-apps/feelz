resource "kubernetes_namespace" "namespace" {
  metadata {
    name = "tehfeelz"
  }
}

resource "kubernetes_config_map_v1" "config" {
  metadata {
    namespace = kubernetes_namespace.namespace.metadata[0].name
    name      = "config"
  }

  data = {
    "unum.json" = jsonencode({
        "name"     = "{{ unum }}"
        "location" = "do"
    })
  }
}

data "digitalocean_database_cluster" "cluster" {
  name = "do-{{ unum }}-unum"
}

resource "digitalocean_database_user" "user" {
  cluster_id = data.digitalocean_database_cluster.cluster.id
  name       = "tehfeelz"
}

resource "kubernetes_secret" "secret" {
  metadata {
    namespace = kubernetes_namespace.namespace.metadata[0].name
    name      = "secret"
  }

  type = "generic"

  data = {
    "mysql.json" = jsonencode({
        "host" =     data.digitalocean_database_cluster.cluster.private_host
        "port" =     data.digitalocean_database_cluster.cluster.port
        "user" =     digitalocean_database_user.user.name
        "password" = digitalocean_database_user.user.password
    })
  }
}

data "kustomization_build" "argocd" {
  path = "argocd"
}

resource "kustomization_resource" "resoures0" {
  for_each = data.kustomization_build.argocd.ids_prio[0]

  manifest = data.kustomization_build.argocd.manifests[each.value]

  depends_on = [kubernetes_namespace.namespace]
}

resource "kustomization_resource" "resoures1" {
  for_each = data.kustomization_build.argocd.ids_prio[1]

  manifest = data.kustomization_build.argocd.manifests[each.value]

  depends_on = [kustomization_resource.resoures0]
}

resource "kustomization_resource" "resoures2" {
  for_each = data.kustomization_build.argocd.ids_prio[2]

  manifest = data.kustomization_build.argocd.manifests[each.value]

  depends_on = [kustomization_resource.resoures1]
}

import docker


class ServerRunDocker:
    def __init__(self, ipa_ddr):
        self.ipa_ddr = ipa_ddr
        self.client = self.connection_docker()

    def connection_docker(self):
        client = docker.DockerClient(base_url=self.ipa_ddr, timeout=80)
        client.ping()
        return client

    def search_image(self, image: str):
        result = self.client.images.search(image)
        return result

    def tag(self, image_name: str, reponame: str, tag: str):
        self.client.images.get(image_name).tag(repository=reponame, tag=tag)

    def pull_image(self, image: str, tag: str):
        self.client.images.pull(repository=image, tag=tag)

    def image_list(self):
        result = self.client.images.list()
        return result

    def container_list(self):
        run_result = self.client.containers.list(all=True)
        return run_result

    def remove_image(self, tag_name: str):
        self.client.images.remove(tag_name)

    def container_kill(self, container_id):
        self.client.containers.get(container_id).kill()

    def start_container(self, container_id):
        self.client.containers.get(container_id).start()

    def container_delete(self, container_id):
        self.client.containers.get(container_id).remove()

    def image_search(self, image_name):
        res = self.client.images.search(image_name)
        return res

    def image_pull(self, image_name):
        image = self.client.images.pull(repository=image_name, tag="latest")
        return image

    def network_list(self):
        return self.client.networks.list()

    def network_delete(self, network_id):
        self.client.networks.get(network_id).remove()

    def network_create(self, name: str, subnet: str = None, gateway: str = None):
        ipam_pool = docker.types.IPAMPool(
            subnet=subnet,
            gateway=gateway
        )
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )
        self.client.networks.create(name=name, ipam=ipam_config, driver="bridge")

    def run_container(self, image, command, ports, env, network_id, name):
        self.client.containers.run(image=image, command=command, ports=ports, environment=env, network=network_id,
                                   detach=True, name=name)

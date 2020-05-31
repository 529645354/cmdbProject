import docker

client = docker.DockerClient(base_url="tcp://192.168.119.131:2375")

image = client.images.pull(repository="centosdasdasdasdf", tag="latest")

print(image)
default: docker-build-distrotv

docker-build-%:
	docker build -t vlc-bridge-$* --build-arg MODULE=$* .

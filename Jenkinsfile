pipeline {
    agent any

    environment {
			GITEA_REPO = 'git@localhost:kivaschenko/graintrade-info.git'  // Local Gitea repository
      DOCKERHUB_CREDENTIALS = '4e1b192b-0c59-4520-a962-74e9d2242bf0'
      DOCKERHUB_NAMESPACE = 'kivaschenko'
      COMMIT_HASH = "${GIT_COMMIT[0..7]}"  // Short Git SHA
			SSH_KEY_ID = '2e02b2c8-fd3d-4f5e-b60b-7604e34b7e1e'
			DEPLOY_USER = 'root'
			DEPLOY_HOST = '65.108.68.57'
			DEPLOY_PATH = '/var/www/graintrade.info'
			COMPOSE_PATH = '/home/deploy/graintrade' // Remote path for docker-compose
    }

    stages {
		stage('Detect Changes') {
			steps {
				scripts {
					backendChanged = sh(script: "git diff --name-only HEAD~1 HEAD | grep '^backend/' || true", returnStdout: true).trim()
					chatChanged = sh(script: "git diff --name-only HEAD~1 HEAD | grep '^chat-room/' || true", returnStdout: true).trim()
					notifyChanged = sh(script: "git diff --name-only HEAD~1 HEAD | grep '^notifications/' || true", returnStdout: true).trim()
					frontendChanged = sh(script: "git diff --name-only HEAD~1 HEAD | grep '^frontend/' || true").trim()
				}
			}
		}
		stage('Build Changed Images') {
			steps {
				script {
					if (backendChanged) {
						sh 'docker build -t backend:ci ./backend'
						sh 'docker save backend:ci | gzip > backend.tar.gz'
					}
					if (chatChanged) {
						sh 'docker build -t chatroom:ci ./chat-room'
						sh 'docker save chatroom:ci | gzip > chatroom.tar.gz'
					}
					if (notifyChanged) {
						sh 'docker build -t notifications:ci ./notifications'
						sh 'docker save '
					}
				}
			}
		}
    }
}
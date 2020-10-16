pipeline {
    agent {
        kubernetes {
            defaultContainer "gitbooks"
            yaml """
            kind: Pod
            metadata:
              name: gitbooks
            spec:
              containers:
              - name: gitbooks
                image: docker.arty-1.base.safe.com/fme-training/gitbooks:2.1.3
                imagePullPolicy: Always
                command:
                - cat
                tty: true
                resources:
                  requests:
                    cpu: 0.5
                    memory: 1024Mi
              restartPolicy: Never
            """
        }
    }
    stages {
        stage('Prepare') {
            steps {
                // fetch npm dependencies from package.json
                sh 'npm install -q'
            }
        }
        stage('Build') {
            steps {
                echo "Building GitBook"
                sh "gitbook build"

                echo "Fixing directory structure"
                sh 'find ./ -type f -exec sed -i \'s/<a href="..\\/">/<a href="..\\/index.html">/g\' {} \\;'

                echo "Generating PDF"
                sh "gitbook pdf ./ ${env.BRANCH_NAME}.pdf"

            }
        }
        stage('Deploy') {
            steps {
                echo "Starting S3 upload"
                withAwsCli(credentialsId: 'gitbook-s3', defaultRegion: 'us-east-1') {
                    // Copy book directory to S3
                    echo "Uploading book"
                    sh "aws s3 cp _book s3://gitbook/${env.BRANCH_NAME} --acl public-read --recursive || true"
                    echo "Uploading PDF"
                    sh "aws s3 cp ${env.BRANCH_NAME}.pdf s3://gitbook/${env.BRANCH_NAME}/ --acl public-read"
                }
            }
        }
    }
}

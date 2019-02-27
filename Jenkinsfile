pipeline {
    agent {
        dockerfile {
            label "docker-xsmall"
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
                sh "find ./ -type f -exec sed -i 's/<a href=\".. \/\">/<a href=\"..\/index.html\">/g' {} \;"                

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
                    sh "aws s3 cp _book s3://gitbook/${env.BRANCH_NAME} --acl public-read --recursive"
                    echo "Uploading PDF"
                    sh "aws s3 cp ${env.BRANCH_NAME}.pdf s3://gitbook/${env.BRANCH_NAME}/ --acl public-read"
                }
            }
        }
    }
}

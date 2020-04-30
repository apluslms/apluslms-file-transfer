# apluslms-file-transfer


[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-%3E%3D%203.5-blue.svg)](https://badge.fury.io/py/lotify)

A package for deploying files from a course directory built by [roman](https://github.com/apluslms/roman)
to a remote server with specific interfaces accepting the files. 

Documentation: https://apluslms-file-transfer.readthedocs.io/.

Currently, [Mooc-grader](https://github.com/apluslms/mooc-grader/tree/cloud-dev) (with `deploy_api`) feature 
and [Static Flie Host](https://github.com/apluslms/static-file-host) are the servers applying the package.
`docker_file_uploader/` provides a docker image applying the package for deploying local files to the server side. 

## Workflow
The figure shows the process of deploying files of a course to a remote server

![Workflow](./doc/workflow.png)
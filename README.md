# VulGPT
An automated vulnerability management tool that uses Neo4j to visualize complex dependency trees and Google OR-Tools to solve for the safest possible package upgrades. Built with Django and React, the system utilizes an asynchronous ETL pipeline to transform standard manifests (requirements.txt, package.json) into actionable remediation roadmaps, ensuring supply chain security through mathematical optimization.

## Quickstart for local docker containerization

```shell
git clone https://github.com/TelloCS/nfl-stats.git
```
## Github Token
Navigate to settings -> Developer Settings at bottom -> Personal access tokens; choose Tokens (Classic) -> then Generate new token (classic)

## IMPORTANT!!!
If no local GPU is present comment out everything in the deploy block in the llm_service
```shell
  llm_service:
    ...
    # Uncomment the below block if you have a local NVIDIA GPU configured for Docker
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Initial command in the root directory
```shell
./manage.sh local
```
To bring down the container
```shell
./manage.sh down-local
```
## Installation
Need to pull the model to be used. (Shouldn't have to restart)
```shell
docker-compose exec llm_service ollama pull qwen2.5-coder
```
## Use Case
Once the environment is live, users can submit standard software manifests (e.g., requirements.txt or package.json) to initiate an automated dependency audit. The system performs a multi-stage analysis to categorize security threats into three tiers: Critical Exploits, Moderate Risks, and Low Priority. For every identified vulnerability, the dashboard provides a mathematically optimized "Safe Version" upgrade path to ensure immediate remediation with minimal breaking changes.

## Credits and references
https://osv.dev/

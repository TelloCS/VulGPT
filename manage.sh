#!/bin/bash

case "$1" in
  local)
    echo "Starting Local Environment in the background..."
    docker compose -f docker-compose.yml up -d --build
    
    echo "Attaching to logs (Press Ctrl+C to exit logs)..."
    docker compose -f docker-compose.yml logs -f
    ;;
    
  down-local)
    echo "Tearing down Local Environment..."
    docker compose -f docker-compose.yml down
    ;;
    
  prod)
    echo "Starting Production Environment in the background..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    
    echo "Attaching to logs (Press Ctrl+C to exit logs)..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
    ;;
    
  down-prod)
    echo "Tearing down Production Environment..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml down
    ;;
    
  clean-frontend)
    echo "Wiping React cache and rebuilding frontend..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml stop frontend nginx
    docker compose -f docker-compose.yml -f docker-compose.prod.yml rm -f frontend nginx
    
    # docker volume rm anilist-app_frontend_static || true
    
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build frontend nginx
    ;;
    
  prune-volumes)
    echo "Clearing orphaned Docker volumes..."
    docker volume prune -f
    ;;

  prune-images)
    echo "Sweeping away dangling (untagged) images..."
    docker image prune -f
    ;;
    
  prune-system)
    echo "NUCLEAR CLEAN: Removing ALL unused containers, networks, and images..."
    # The -a flag removes ALL unused images, not just dangling ones.
    # The --volumes flag is NOT included here, so your database is still 100% safe.
    docker system prune -a -f
    ;;
    
  *)
    echo "Invalid command. Please use one of the following:"
    echo "Usage: ./manage.sh {local|prod|down-local|down-prod|clean-frontend|prune-volumes}"
    exit 1
esac
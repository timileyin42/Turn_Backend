@echo off
REM TURN Docker Management Scripts for Windows
REM Usage: scripts\docker.bat [command]

setlocal EnableDelayedExpansion

REM Check if Docker and Docker Compose are installed
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

where docker-compose >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Get command from first argument
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=help

if "%COMMAND%"=="dev" goto :dev
if "%COMMAND%"=="prod" goto :prod
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="clean" goto :clean
if "%COMMAND%"=="logs" goto :logs
if "%COMMAND%"=="db-migrate" goto :db_migrate
if "%COMMAND%"=="db-reset" goto :db_reset
if "%COMMAND%"=="build" goto :build
if "%COMMAND%"=="health" goto :health
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="exec" goto :exec_app
if "%COMMAND%"=="help" goto :help
goto :unknown

:dev
echo [INFO] Starting development environment...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile development up -d
echo [SUCCESS] Development environment started!
echo [INFO] API: http://localhost:8000
echo [INFO] Docs: http://localhost:8000/docs
echo [INFO] pgAdmin: http://localhost:5050 (admin@turn.com / admin123)
echo [INFO] Redis Commander: http://localhost:8081
goto :end

:prod
echo [INFO] Starting production environment...
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
echo [SUCCESS] Production environment started!
echo [INFO] API: http://localhost:80
goto :end

:stop
echo [INFO] Stopping all services...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml down
echo [SUCCESS] All services stopped!
goto :end

:clean
echo [WARNING] This will remove all TURN containers, volumes, and images. Are you sure? (y/N)
set /p response=
if /i "!response!"=="y" (
    echo [INFO] Cleaning up Docker resources...
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.prod.yml down -v --remove-orphans
    for /f "tokens=3" %%i in ('docker images ^| findstr turn_') do docker rmi -f %%i 2>nul
    for /f "tokens=2" %%i in ('docker volume ls ^| findstr turn_') do docker volume rm %%i 2>nul
    echo [SUCCESS] Cleanup completed!
) else (
    echo [INFO] Cleanup cancelled.
)
goto :end

:logs
set SERVICE=%2
if "%SERVICE%"=="" set SERVICE=app
echo [INFO] Showing logs for service: !SERVICE!
docker-compose logs -f !SERVICE!
goto :end

:db_migrate
echo [INFO] Running database migrations...
docker-compose exec app alembic upgrade head
echo [SUCCESS] Database migrations completed!
goto :end

:db_reset
echo [WARNING] This will reset the database. Are you sure? (y/N)
set /p response=
if /i "!response!"=="y" (
    echo [INFO] Resetting database...
    docker-compose exec app python init_db.py drop
    docker-compose exec app python init_db.py create
    docker-compose exec app alembic upgrade head
    echo [SUCCESS] Database reset completed!
) else (
    echo [INFO] Database reset cancelled.
)
goto :end

:build
echo [INFO] Building TURN application image...
docker build -t turn-backend:latest .
echo [SUCCESS] Build completed!
goto :end

:health
echo [INFO] Checking service health...
docker-compose ps | findstr /c:"app" | findstr /c:"Up" >nul && echo [SUCCESS] app is running || echo [ERROR] app is not running
docker-compose ps | findstr /c:"db" | findstr /c:"Up" >nul && echo [SUCCESS] db is running || echo [ERROR] db is not running
docker-compose ps | findstr /c:"redis" | findstr /c:"Up" >nul && echo [SUCCESS] redis is running || echo [ERROR] redis is not running
goto :end

:status
echo [INFO] Docker Compose Status:
docker-compose ps
echo.
echo [INFO] Docker Images:
docker images | findstr /r "turn_ postgres redis nginx"
echo.
echo [INFO] Docker Volumes:
docker volume ls | findstr turn_
goto :end

:exec_app
shift
docker-compose exec app %*
goto :end

:help
echo TURN Docker Management Script
echo.
echo Usage: %0 [command]
echo.
echo Commands:
echo   dev          Start development environment with hot reload
echo   prod         Start production environment
echo   stop         Stop all services
echo   clean        Remove all containers, volumes, and images
echo   logs [service] Show logs for service (default: app)
echo   db-migrate   Run database migrations
echo   db-reset     Reset database (drop and recreate)
echo   build        Build application image
echo   health       Check service health
echo   status       Show status of all services
echo   exec [cmd]   Execute command in app container
echo   help         Show this help message
echo.
echo Examples:
echo   %0 dev                    # Start development environment
echo   %0 logs app               # Show app logs
echo   %0 exec python manage.py  # Run command in container
goto :end

:unknown
echo [ERROR] Unknown command: %COMMAND%
goto :help

:end
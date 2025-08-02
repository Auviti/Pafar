#!/bin/bash

# Complete Integration Test Runner for Pafar Transport Management System
# This script runs all integration tests across backend, frontend, and mobile platforms

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

# Function to record test result
record_test_result() {
    local test_name="$1"
    local result="$2"
    local duration="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        success "$test_name completed in ${duration}s"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        error "$test_name failed after ${duration}s"
    fi
    
    TEST_RESULTS+=("$test_name:$result:$duration")
}

# Function to check if service is running
check_service() {
    local service_name="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1
    
    log "Checking if $service_name is running at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            success "$service_name is running"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to start backend server
start_backend() {
    log "Starting backend server..."
    
    cd backend
    
    # Set up virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    log "Installing backend dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Set environment variables for testing
    export TESTING=true
    export DATABASE_URL="sqlite:///./test_pafar.db"
    export REDIS_URL="redis://localhost:6379/1"
    export SECRET_KEY="test-secret-key-for-integration-testing"
    export STRIPE_SECRET_KEY="sk_test_fake_key_for_testing"
    
    # Start the server in background
    log "Starting FastAPI server..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    BACKEND_PID=$!
    
    cd ..
    
    # Wait for server to be ready
    if check_service "Backend API" "http://localhost:8000/health"; then
        return 0
    else
        return 1
    fi
}

# Function to start frontend server
start_frontend() {
    log "Starting frontend server..."
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log "Installing frontend dependencies..."
        npm install > /dev/null 2>&1
    fi
    
    # Set environment variables
    export REACT_APP_API_URL="http://localhost:8000"
    export REACT_APP_WS_URL="ws://localhost:8000"
    export NODE_ENV="test"
    
    # Start the server in background
    log "Starting React development server..."
    npm start > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    cd ..
    
    # Wait for server to be ready
    if check_service "Frontend" "http://localhost:3000"; then
        return 0
    else
        return 1
    fi
}

# Function to start Redis server
start_redis() {
    log "Starting Redis server..."
    
    # Check if Redis is already running
    if pgrep redis-server > /dev/null; then
        log "Redis server is already running"
        return 0
    fi
    
    # Start Redis server
    redis-server --port 6379 --daemonize yes > /dev/null 2>&1
    
    # Wait for Redis to be ready
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        success "Redis server started successfully"
        return 0
    else
        error "Failed to start Redis server"
        return 1
    fi
}

# Function to run backend tests
run_backend_tests() {
    log "Running backend integration tests..."
    
    cd backend
    source .venv/bin/activate
    
    # Run API integration tests
    local start_time=$(date +%s)
    if python -m pytest tests/test_e2e_integration_complete.py -v --tb=short > backend_test_results.log 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Backend API Integration" "PASS" "$duration"
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Backend API Integration" "FAIL" "$duration"
        warning "Backend test output saved to backend/backend_test_results.log"
    fi
    
    # Run load tests
    start_time=$(date +%s)
    if python -m pytest tests/performance/load_test_complete.py -v -m load_test > load_test_results.log 2>&1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        record_test_result "Backend Load Tests" "PASS" "$duration"
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        record_test_result "Backend Load Tests" "FAIL" "$duration"
        warning "Load test output saved to backend/load_test_results.log"
    fi
    
    cd ..
}

# Function to run frontend tests
run_frontend_tests() {
    log "Running frontend E2E tests..."
    
    cd frontend
    
    # Run E2E tests with Playwright
    local start_time=$(date +%s)
    if npm run test:e2e > frontend_e2e_results.log 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Frontend E2E Tests" "PASS" "$duration"
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Frontend E2E Tests" "FAIL" "$duration"
        warning "Frontend E2E test output saved to frontend/frontend_e2e_results.log"
    fi
    
    # Run component integration tests
    start_time=$(date +%s)
    if npm run test:integration > frontend_integration_results.log 2>&1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        record_test_result "Frontend Integration Tests" "PASS" "$duration"
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        record_test_result "Frontend Integration Tests" "FAIL" "$duration"
        warning "Frontend integration test output saved to frontend/frontend_integration_results.log"
    fi
    
    cd ..
}

# Function to run mobile tests
run_mobile_tests() {
    log "Running mobile integration tests..."
    
    # Check if Flutter is installed
    if ! command -v flutter &> /dev/null; then
        warning "Flutter not found. Skipping mobile tests."
        return 0
    fi
    
    cd mobile
    
    # Get dependencies
    log "Getting Flutter dependencies..."
    flutter pub get > /dev/null 2>&1
    
    # Generate mocks
    log "Generating test mocks..."
    flutter packages pub run build_runner build --delete-conflicting-outputs > /dev/null 2>&1
    
    # Run integration tests
    local start_time=$(date +%s)
    if flutter test test/integration/complete_app_integration_test.dart > mobile_integration_results.log 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Mobile Integration Tests" "PASS" "$duration"
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Mobile Integration Tests" "FAIL" "$duration"
        warning "Mobile integration test output saved to mobile/mobile_integration_results.log"
    fi
    
    # Run widget tests
    start_time=$(date +%s)
    if flutter test --coverage > mobile_widget_results.log 2>&1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        record_test_result "Mobile Widget Tests" "PASS" "$duration"
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        record_test_result "Mobile Widget Tests" "FAIL" "$duration"
        warning "Mobile widget test output saved to mobile/mobile_widget_results.log"
    fi
    
    cd ..
}

# Function to run cross-platform tests
run_cross_platform_tests() {
    log "Running cross-platform integration tests..."
    
    cd backend
    source .venv/bin/activate
    
    local start_time=$(date +%s)
    if python -m pytest tests/test_e2e_integration_complete.py::TestCompleteSystemIntegration::test_cross_platform_data_synchronization -v > cross_platform_results.log 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Cross-Platform Integration" "PASS" "$duration"
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Cross-Platform Integration" "FAIL" "$duration"
        warning "Cross-platform test output saved to backend/cross_platform_results.log"
    fi
    
    cd ..
}

# Function to run performance tests
run_performance_tests() {
    log "Running performance and stress tests..."
    
    cd backend
    source .venv/bin/activate
    
    local start_time=$(date +%s)
    if timeout 1800 python -m pytest tests/performance/load_test_complete.py -v -m stress_test > stress_test_results.log 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Performance Stress Tests" "PASS" "$duration"
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "Performance Stress Tests" "FAIL" "$duration"
        warning "Stress test output saved to backend/stress_test_results.log"
    fi
    
    cd ..
}

# Function to validate system health
validate_system_health() {
    log "Validating system health..."
    
    local health_checks=0
    local health_passed=0
    
    # Check API health
    health_checks=$((health_checks + 1))
    if curl -s "http://localhost:8000/health" | grep -q "ok"; then
        health_passed=$((health_passed + 1))
        success "API health check passed"
    else
        error "API health check failed"
    fi
    
    # Check database connectivity
    health_checks=$((health_checks + 1))
    if curl -s "http://localhost:8000/api/v1/health/db" | grep -q "ok"; then
        health_passed=$((health_passed + 1))
        success "Database health check passed"
    else
        error "Database health check failed"
    fi
    
    # Check Redis connectivity
    health_checks=$((health_checks + 1))
    if redis-cli ping > /dev/null 2>&1; then
        health_passed=$((health_passed + 1))
        success "Redis health check passed"
    else
        error "Redis health check failed"
    fi
    
    # Check frontend accessibility
    health_checks=$((health_checks + 1))
    if curl -s "http://localhost:3000" > /dev/null 2>&1; then
        health_passed=$((health_passed + 1))
        success "Frontend health check passed"
    else
        error "Frontend health check failed"
    fi
    
    local start_time=$(date +%s)
    if [ $health_passed -eq $health_checks ]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "System Health Validation" "PASS" "$duration"
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        record_test_result "System Health Validation" "FAIL" "$duration"
    fi
}

# Function to generate test report
generate_report() {
    local report_file="integration_test_report.md"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    log "Generating test report..."
    
    cat > "$report_file" << EOF
# Pafar Integration Test Report

**Generated:** $timestamp  
**Total Tests:** $TOTAL_TESTS  
**Passed:** $PASSED_TESTS  
**Failed:** $FAILED_TESTS  
**Success Rate:** $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%

## Test Results Summary

EOF
    
    for result in "${TEST_RESULTS[@]}"; do
        IFS=':' read -r test_name test_result test_duration <<< "$result"
        if [ "$test_result" = "PASS" ]; then
            echo "✅ **$test_name** - PASSED (${test_duration}s)" >> "$report_file"
        else
            echo "❌ **$test_name** - FAILED (${test_duration}s)" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

## System Information

- **Backend API:** http://localhost:8000
- **Frontend Web:** http://localhost:3000
- **Redis Cache:** localhost:6379
- **Test Database:** SQLite (test_pafar.db)

## Test Logs

- Backend API Integration: \`backend/backend_test_results.log\`
- Backend Load Tests: \`backend/load_test_results.log\`
- Frontend E2E Tests: \`frontend/frontend_e2e_results.log\`
- Frontend Integration: \`frontend/frontend_integration_results.log\`
- Mobile Integration: \`mobile/mobile_integration_results.log\`
- Mobile Widget Tests: \`mobile/mobile_widget_results.log\`
- Cross-Platform Tests: \`backend/cross_platform_results.log\`
- Performance Tests: \`backend/stress_test_results.log\`

## Recommendations

EOF
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo "🎉 All tests passed! The system is ready for production deployment." >> "$report_file"
    else
        echo "⚠️ Some tests failed. Please review the failed tests and fix issues before deployment." >> "$report_file"
        echo "" >> "$report_file"
        echo "### Failed Tests:" >> "$report_file"
        for result in "${TEST_RESULTS[@]}"; do
            IFS=':' read -r test_name test_result test_duration <<< "$result"
            if [ "$test_result" = "FAIL" ]; then
                echo "- $test_name" >> "$report_file"
            fi
        done
    fi
    
    success "Test report generated: $report_file"
}

# Function to cleanup processes
cleanup() {
    log "Cleaning up test environment..."
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Stop Redis if we started it
    if pgrep redis-server > /dev/null; then
        redis-cli shutdown 2>/dev/null || true
    fi
    
    # Clean up test database
    rm -f backend/test_pafar.db 2>/dev/null || true
    
    success "Cleanup completed"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    log "Starting Pafar Complete Integration Test Suite"
    log "=============================================="
    
    # Start services
    if ! start_redis; then
        error "Failed to start Redis server"
        exit 1
    fi
    
    if ! start_backend; then
        error "Failed to start backend server"
        exit 1
    fi
    
    if ! start_frontend; then
        error "Failed to start frontend server"
        exit 1
    fi
    
    # Validate system health before running tests
    validate_system_health
    
    # Run all test suites
    run_backend_tests
    run_frontend_tests
    run_mobile_tests
    run_cross_platform_tests
    run_performance_tests
    
    # Generate final report
    generate_report
    
    # Print summary
    log "=============================================="
    log "Integration Test Suite Completed"
    log "Total Tests: $TOTAL_TESTS"
    log "Passed: $PASSED_TESTS"
    log "Failed: $FAILED_TESTS"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        success "🎉 All integration tests passed!"
        log "The Pafar Transport Management System is ready for production deployment."
        exit 0
    else
        error "❌ Some integration tests failed."
        log "Please review the test report and fix issues before deployment."
        exit 1
    fi
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
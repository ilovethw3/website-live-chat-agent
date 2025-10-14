#!/bin/bash
# 测试运行脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}  Website Live Chat Agent Tests  ${NC}"
echo -e "${BLUE}==================================${NC}"
echo

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# 检查依赖
echo -e "${YELLOW}Checking test dependencies...${NC}"
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -e ".[dev]"
fi

# 运行不同类型的测试
case "${1:-all}" in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        pytest tests/unit/ -v
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        pytest tests/integration/ -v
        ;;
    e2e)
        echo -e "${GREEN}Running E2E tests...${NC}"
        pytest tests/e2e/ -v
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage...${NC}"
        pytest --cov=src --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}Coverage report generated at: htmlcov/index.html${NC}"
        ;;
    quick)
        echo -e "${GREEN}Running quick tests (no coverage)...${NC}"
        pytest tests/ -x --tb=short
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest tests/ -v
        ;;
    *)
        echo "Usage: $0 {unit|integration|e2e|coverage|quick|all}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}✅ Tests completed!${NC}"


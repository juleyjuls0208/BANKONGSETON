#!/bin/bash
# Build iOS IPA Script
# This script helps trigger the iOS build in CI/CD

set -e

echo "=========================================="
echo "BankongSeton Student iOS IPA Builder"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "mobile/ios/BankongSetonStudent" ]; then
    echo -e "${RED}Error: Not in the project root directory${NC}"
    exit 1
fi

echo -e "${GREEN}Project structure verified${NC}"

# Display build options
echo ""
echo "Build Options:"
echo "1. Build for Simulator (no code signing required)"
echo "2. Build IPA for Sideloading (requires code signing)"
echo "3. Show Codemagic setup instructions"
echo "4. Show GitHub Actions instructions"
echo ""

read -p "Select an option (1-4): " option

case $option in
    1)
        echo -e "${GREEN}Building for simulator...${NC}"
        echo ""
        echo "To build for simulator, use Codemagic with the ios-student-app-simulator workflow."
        echo "Push to main branch or the gsd/* branch to trigger automatic build."
        echo ""
        echo "Or manually trigger via Codemagic dashboard:"
        echo "  1. Go to https://codemagic.io/apps"
        echo "  2. Select your app"
        echo "  3. Click 'Start new build'"
        echo "  4. Select workflow: 'BankongSeton Student iOS (Simulator)'"
        ;;
    2)
        echo -e "${YELLOW}Building IPA for sideloading...${NC}"
        echo ""
        echo "To build IPA for sideloading, you need:"
        echo ""
        echo "Prerequisites:"
        echo "  1. Apple Developer Account (\$99/year)"
        echo "  2. Code signing certificate"
        echo "  3. Provisioning profile"
        echo ""
        echo "Option A: Use Codemagic (Recommended)"
        echo "  1. Go to https://codemagic.io"
        echo "  2. Create account and connect repository"
        echo "  3. Add environment variables:"
        echo "     - APPLE_ID (your Apple Developer email)"
        echo "     - APPLE_APP_SPECIFIC_PASSWORD"
        echo "     - APPLE_TEAM_ID (from Apple Developer Portal)"
        echo "  4. Start build with 'ios-student-app-sideload' workflow"
        echo ""
        echo "Option B: Use GitHub Actions"
        echo "  1. Add secrets to your GitHub repository:"
        echo "     - CERTIFICATE_DATA (base64 encoded .p12)"
        echo "     - CERTIFICATE_PASSWORD"
        echo "     - PROVISIONING_PROFILE_DATA (base64 encoded .mobileprovision)"
        echo "     - APPLE_TEAM_ID"
        echo "  2. Go to Actions tab"
        echo "  3. Run workflow: 'Build iOS IPA (Sideload)'"
        echo ""
        echo "See docs/BUILD_IPA_WITHOUT_MAC.md for detailed instructions."
        ;;
    3)
        echo -e "${GREEN}Codemagic Setup Instructions${NC}"
        echo ""
        cat docs/BUILD_IPA_WITHOUT_MAC.md | grep -A 100 "Option 1: Use Codemagic"
        ;;
    4)
        echo -e "${GREEN}GitHub Actions Setup Instructions${NC}"
        echo ""
        cat docs/BUILD_IPA_WITHOUT_MAC.md | grep -A 50 "Option 2: GitHub Actions"
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"

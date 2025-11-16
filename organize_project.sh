#!/bin/bash
# Hospital Dashboard - Project Organization Script
# Run this to organize documentation into folders

echo "================================================"
echo "Hospital Dashboard - Project Organization"
echo "================================================"
echo ""

# Create documentation folders
echo "Creating documentation structure..."
mkdir -p docs/user-guides
mkdir -p docs/technical
mkdir -p docs/archive
mkdir -p docs/reference

echo "✓ Created docs/ folder structure"
echo ""

# Move user guides
echo "Moving user guides..."
mv QUICKSTART.md docs/user-guides/ 2>/dev/null
mv AUTH_QUICKSTART.md docs/user-guides/ 2>/dev/null
mv DEPLOY_QUICKSTART.md docs/user-guides/ 2>/dev/null
mv DASHBOARD_WORKSHEETS_GUIDE.md docs/user-guides/ 2>/dev/null
mv VALUATION_DASHBOARD_GUIDE.md docs/user-guides/ 2>/dev/null
echo "✓ Moved 5 user guides"

# Move technical documentation
echo "Moving technical documentation..."
mv TECHNICAL_ARCHITECTURE.md docs/technical/ 2>/dev/null
mv KPI_HIERARCHY_DOCUMENTATION.md docs/technical/ 2>/dev/null
mv AUTHENTICATION_GUIDE.md docs/technical/ 2>/dev/null
mv DEPLOYMENT_GUIDE.md docs/technical/ 2>/dev/null
echo "✓ Moved 4 technical docs"

# Move reference materials
echo "Moving reference materials..."
mv HCRIS_QUICK_REFERENCE.md docs/reference/ 2>/dev/null
mv HCRIS_VALUATION_METHODOLOGY.md docs/reference/ 2>/dev/null
mv DATA_STRUCTURE_FOR_ANALYSTS.md docs/reference/ 2>/dev/null
echo "✓ Moved 3 reference docs"

# Archive old documentation
echo "Archiving old documentation..."
mv ETL_MULTI_STATE_UPDATE.md docs/archive/ 2>/dev/null
mv ETL_REDESIGN_SUMMARY.md docs/archive/ 2>/dev/null
mv WORKSHEET_ETL_BATCH.md docs/archive/ 2>/dev/null
mv DATABASE_BUILD_COMPLETE.md docs/archive/ 2>/dev/null
mv FOLDER_STRUCTURE.txt docs/archive/ 2>/dev/null
echo "✓ Moved 5 docs to archive"

echo ""
echo "================================================"
echo "Files in Root Directory (should be minimal):"
echo "================================================"
ls -1 *.md 2>/dev/null | head -10
echo ""

echo "================================================"
echo "Documentation Structure:"
echo "================================================"
tree docs/ -L 2 2>/dev/null || find docs/ -type f | sort

echo ""
echo "================================================"
echo "Organization Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Review organized structure"
echo "2. Update README.md links to new locations"
echo "3. Commit changes: git add docs/ && git commit -m 'Organize documentation'"
echo ""

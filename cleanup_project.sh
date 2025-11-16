#!/bin/bash
# Hospital Dashboard - Project Cleanup Script
# Removes unnecessary test files and duplicates

echo "================================================"
echo "Hospital Dashboard - Project Cleanup"
echo "================================================"
echo ""
echo "This will remove the following files:"
echo "  - test_dash.py (test file)"
echo "  - test_dashboard_data.py (test file)"
echo "  - extract_pdf_text.py (test utility)"
echo "  - requirements_auth.txt (merged into requirements.txt)"
echo "  - to_do.txt (completed task list)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cleanup cancelled."
    exit 1
fi

echo ""
echo "Removing files..."

# Remove test files
if [ -f "test_dash.py" ]; then
    rm test_dash.py
    echo "✓ Removed test_dash.py"
fi

if [ -f "test_dashboard_data.py" ]; then
    rm test_dashboard_data.py
    echo "✓ Removed test_dashboard_data.py"
fi

if [ -f "extract_pdf_text.py" ]; then
    rm extract_pdf_text.py
    echo "✓ Removed extract_pdf_text.py"
fi

# Remove merged requirements file
if [ -f "requirements_auth.txt" ]; then
    rm requirements_auth.txt
    echo "✓ Removed requirements_auth.txt (merged into requirements.txt)"
fi

# Remove completed task list
if [ -f "to_do.txt" ]; then
    rm to_do.txt
    echo "✓ Removed to_do.txt (tasks completed)"
fi

# Optional: Remove large reference file
echo ""
read -p "Remove 'Provider Reimbursement Manual.txt' (large reference file)? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "Provider Reimbursement Manual.txt" ]; then
        rm "Provider Reimbursement Manual.txt"
        echo "✓ Removed Provider Reimbursement Manual.txt"
    fi
fi

echo ""
echo "================================================"
echo "Cleanup Complete!"
echo "================================================"
echo ""
echo "Files removed. You may want to run:"
echo "  git status"
echo "  git add -u"
echo "  git commit -m 'Clean up test files and duplicates'"
echo ""

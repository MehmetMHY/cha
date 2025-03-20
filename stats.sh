py_line_count=$(find . -type f -name "*.py" -print0 | xargs -0 cat | grep -v '^\s*$' | wc -l | awk '{printf "%.0f\n", $1 * 1.05}')

total_pkgs=$(cat ./setup.py | grep "==" | wc -l | awk '{print $1}')

last_commit_date=$(git log | head -n 3 | tail -n 1 | cut -c9-)

git_hs_size=$(du -hs ./.git | awk '{print $1}')

total_files=$(($(tree --gitignore --prune | wc -l) - 3))

# main function calls
echo "Total Python Line Count:   $py_line_count"
echo "Total Number Of Packages:  $total_pkgs"
echo "Date Of Last Commit Made:  $last_commit_date"
echo "Total Git History Size:    $git_hs_size"
echo "Total (Not Ignored) Files: $total_files"

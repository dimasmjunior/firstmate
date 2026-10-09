set -eu
. tests/fm-review-diff.test.sh
unset FM_TEST_SEAM FM_GATE_REFUSE_BYPASS
case_dir=$(make_case live-evidence)
stale_and_mr_commits "$case_dir" 7
stale=$(git -C "$case_dir/wt" rev-parse HEAD)
write_task_meta "$case_dir" 'mode=no-mistakes' 'kind=ship' 'pr=https://gitlab.example/group/subgroup/project/-/merge_requests/7' "pr_head=$stale"
export FM_HOME="$case_dir" FM_STATE_OVERRIDE="$case_dir/state"
evidence=/home/dimas/.no-mistakes/evidence/01M4HAFFSRF3Y6RJPFA65NYNVS/live-product.txt
{
  echo 'Published fix outranks stale local branch and recorded head'
  run_review_diff "$case_dir" task-x1
  echo 'Delete source branch; MR ref remains reviewable'
  git -C "$case_dir/wt" push -q origin mr-head-tmp:refs/heads/source
  git -C "$case_dir/wt" push -q origin --delete source
  run_review_diff "$case_dir" task-x1
  echo 'Register ready record from real project remote'
  "$ROOT/bin/fm-pr-check.sh" task-x1 https://gitlab.example/group/subgroup/project/-/merge_requests/7
  grep '^pr' "$case_dir/state/task-x1.meta"
  grep -qx "pr_head=$MR_SHA" "$case_dir/state/task-x1.meta"
  echo 'Publish another fix after registration'
  git -C "$case_dir/wt" checkout -q mr-head-tmp
  printf 'second-published-fix\n' > "$case_dir/wt/feature.txt"
  git -C "$case_dir/wt" commit -qam 'second fix'
  second=$(git -C "$case_dir/wt" rev-parse HEAD)
  git -C "$case_dir/wt" push -q origin HEAD:refs/merge-requests/7/head
  git -C "$case_dir/wt" checkout -q fm/task-x1
  run_review_diff "$case_dir" task-x1
  "$ROOT/bin/fm-pr-check.sh" task-x1 https://gitlab.example/group/subgroup/project/-/merge_requests/7
  grep '^pr' "$case_dir/state/task-x1.meta"
  grep -qx "pr_head=$second" "$case_dir/state/task-x1.meta"
  echo 'Remove remote MR ref: review falls back to recorded head'
  git -C "$case_dir/wt" push -q origin :refs/merge-requests/7/head
  run_review_diff "$case_dir" task-x1
  echo 'Re-register unreadable head: no pr_head is recorded'
  "$ROOT/bin/fm-pr-check.sh" task-x1 https://gitlab.example/group/subgroup/project/-/merge_requests/7
  grep '^pr' "$case_dir/state/task-x1.meta"
  if grep -q '^pr_head=' "$case_dir/state/task-x1.meta"; then exit 1; fi
  echo 'Without recorded or published head: explicit warning and local diff'
  run_review_diff "$case_dir" task-x1
} > "$evidence" 2>&1

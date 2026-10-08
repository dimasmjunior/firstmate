#!/bin/bash
set -eu
R=$PWD
E=/home/dimas/.no-mistakes/evidence/01M4DS4Q9EA0N68CM3Q1SX7CMA
export HOME="$R/.live-validation/local-user" GLAB_CONFIG_DIR="$R/.live-validation/local-glab" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
unset FM_ROOT_OVERRIDE FM_STATE_OVERRIDE FM_DATA_OVERRIDE FM_CONFIG_OVERRIDE FM_PROJECTS_OVERRIDE
mkdir -p "$HOME" "$GLAB_CONFIG_DIR"
export FM_HOME="$R/.live-validation/local-home"
rm -rf "$FM_HOME"
bin/fm-lab-home.sh create "$FM_HOME"
printf 'manual\n' > "$FM_HOME/config/backlog-backend"
printf '%s\n' '- project [direct-PR +yolo branch=topic/ forge=gitlab] - disposable' > "$FM_HOME/data/projects.md"
printf '\nREGISTERED POSTURE\n'
bin/fm-project-mode.sh project
bin/fm-project-mode.sh --forge project
bin/fm-project-mode.sh --branch-prefix project
printf '\nGITLAB BRIEF\n'
bin/fm-brief.sh lab-gl project --mode direct-PR --forge gitlab --branch-prefix topic/
cp "$FM_HOME/data/lab-gl/brief.md" "$E/generated-gitlab-brief.md"
printf '\nGITHUB NAMED BASE\n'
bin/fm-brief.sh lab-gh project --mode direct-PR --base-branch release
cp "$FM_HOME/data/lab-gh/brief.md" "$E/generated-github-brief.md"
printf '\nBOUND NAMED BASE REFUSAL\n'
if bin/fm-brief.sh lab-base project --mode direct-PR --forge gitlab --base-branch release; then exit 1; fi
printf '\nGERRIT BRIEF\n'
bin/fm-brief.sh lab-gerrit project --mode direct-PR --forge gerrit
cp "$FM_HOME/data/lab-gerrit/brief.md" "$E/generated-gerrit-brief.md"
git init -q "$FM_HOME/projects/project"
git -C "$FM_HOME/projects/project" remote add origin https://dummy-secret@gitlab.example.test/group/project.git
printf '\nCREDENTIAL-SAFE PROPOSAL\n'
bin/fm-forge-detect.sh "$FM_HOME/projects/project"
printf '\nGERRIT PRECEDENCE\n'
git -C "$FM_HOME/projects/project" config remote.origin.push HEAD:refs/for/main
bin/fm-forge-detect.sh "$FM_HOME/projects/project"
git -C "$FM_HOME/projects/project" config --unset remote.origin.push
printf '\nBOOTSTRAP LOCAL DETECTION\n'
FM_BOOTSTRAP_DETECT_ONLY=1 bin/fm-bootstrap.sh

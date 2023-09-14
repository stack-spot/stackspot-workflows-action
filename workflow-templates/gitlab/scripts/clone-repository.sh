#!/usr/bin/env bash
repo_name=$1
workspace_pat=$2
email=$3
workspace_name=$4
folder_name=$5

echo "Cloning repo $repo_name";
remote=https://x-token-auth:$workspace_pat@gitlab.com/$workspace_name/$repo_name.git
remote_app=https://gitlab.com/$workspace_name/$repo_name.git

echo "Turning off Git's http.sslVerify"
git config --global http.sslVerify "false"

echo git clone $remote_app $folder_name;
git clone $remote $folder_name;

echo "Set git username";
echo git config --global user.email "$email";
echo git config --global user.name "$email";

git config --global user.email "$email";
git config --global user.name "$email";

cd $folder_name;
exist_branch_main=$(git branch -a | grep -m1 "remotes/origin/main")
if [ -n "$exist_branch_main" ] && [ "$exist_branch_main" != "null" ]; then
  cd ..;
  # branch exists
  exit 0;
fi

echo -e "\nCreating branch main"
git branch -M main;
touch .gitignore;
git add .;
git commit -am "First commit";
git push origin main;
cd ..;
exit 0;
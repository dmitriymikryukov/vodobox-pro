#!/bin/bash
echo "pushing..."
COMMIT_NAME="very-very important update"
git add *
git commit -m "$COMMIT_NAME"
git push

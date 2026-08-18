# Upload this folder to GitHub

1. Create an empty public or private repository. Do not initialize it with a README.
2. Copy the contents of GitHub_Code_Deposit, not the parent Chinese working directory.
3. Add a licence file on GitHub if the institution has chosen one. MIT or Apache-2.0 is typical for this code.
4. Do not commit author names, ORCID iDs, the manuscript, Zenodo data files, or local paths.
5. After the first push, create a version tag such as v1.0.0 and, if needed, archive that release to Zenodo as the code DOI.
6. Paste the repository URL into the manuscript Code Availability statement.

Suggested first commands, run inside GitHub_Code_Deposit:

    git init
    git add .
    git commit -m "Add HFFM analysis code"
    git branch -M main
    git remote add origin [repository-url]
    git push -u origin main

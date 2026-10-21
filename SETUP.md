# Setup

1. Create a **public repository named exactly `Manohar-P-C`** at https://github.com/Manohar-P-C.
2. Extract this ZIP and upload all files and folders to the repository root.
3. In `README.md`, replace `YOUR_GITHUB_USERNAME`, `YOUR_LINKEDIN`, and `YOUR_PORTFOLIO_URL`.
4. Commit and push to the `main` branch.
5. Open **Settings → Actions → General → Workflow permissions**, and enable **Read and write permissions**.
6. Open **Actions → Update profile art → Run workflow** once. The workflow fetches contribution-day data from the repository owner's public GitHub profile and refreshes the SVG cards.
7. The workflow also runs daily.

## Notes

- The contribution data is fetched from GitHub's public contributions page. The profile repository must belong to the account whose data you want to show.
- The portrait SVG is generated from `source-photo.png`. To change your portrait later, replace that file and rerun `python scripts/make_ascii_svg.py`.
- GitHub profile stats may take a short time to update after workflow completion.
- Never add a personal access token to the repository for this public-page fetch method.

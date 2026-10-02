# scripts

`download_data.sh` downloads the Olist dataset from Kaggle into `data/` using the Kaggle command-line tool. It needs the CLI installed and an API token configured.

On Windows, run the equivalent command directly in PowerShell:

```powershell
kaggle datasets download -d olistbr/brazilian-ecommerce -p data --unzip
```

The CSVs and the database built from them are not committed to the repository. Run `python -m olist_agent.build_db` after downloading.
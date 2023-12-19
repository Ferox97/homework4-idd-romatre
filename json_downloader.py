import subprocess
import concurrent.futures

# Percorso del file con gli identificatori PMC
file_path = 'C:\\Users\\Fero\\Desktop\\HW4\\pmcid_101800_152700.txt'

# Numero massimo di thread da eseguire contemporaneamente
MAX_THREADS = 100

def download_file(pmc_id):
    command = f'aws s3 cp s3://pmc-oa-opendata/oa_comm/xml/all/{pmc_id}.xml . --no-sign-request'
    subprocess.run(command, shell=True)

# Legge gli identificatori PMC dal file
with open(file_path, 'r') as file:
    pmc_ids = file.read().strip('[]').replace("'", "").split(', ')

# Utilizza un ThreadPoolExecutor per scaricare in parallelo
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    executor.map(download_file, pmc_ids)

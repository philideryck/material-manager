import pandas as pd

def exporter_distributions(distributions, path='transferts.csv'):
    df = pd.DataFrame(distributions)
    df.to_csv(path, index=False)
    print(f"Exporté vers {path}")

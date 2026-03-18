import pandas as pd

df = pd.read_csv("C:/projects/phishguard-nlp/data/SMSSpamCollection", sep='\t', header=None)
df.columns = ["label", "message"]

df.to_csv("spam.csv", index=False)
print("Converted to spam.csv")
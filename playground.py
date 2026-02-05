from pyopensky.rest import REST
import pandas as pd

rest = REST()

# Get current state vectors for all aircraft
all = rest.states()

df_all = pd.DataFrame(all)

print(df_all[df_all["origin_country"] == "Poland"])

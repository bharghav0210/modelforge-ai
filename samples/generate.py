"""Original noisy synthetic examples, seed 42. Never used as benchmark claims."""
from pathlib import Path
import numpy as np
import pandas as pd

out = Path(__file__).parent
rng = np.random.default_rng(42)
n = 240
age = rng.integers(18, 76, n)
tenure = rng.integers(1, 73, n)
monthly = rng.uniform(20, 140, n).round(2)
contract = rng.choice(['monthly', 'annual', 'two-year'], n)
logit = -0.4 + .018*(monthly-65) - .025*(tenure-24) + .7*(contract=='monthly')
churn = rng.random(n) < 1/(1+np.exp(-logit))
pd.DataFrame({'age': age, 'tenure_months': tenure, 'monthly_charge': monthly, 'contract': contract, 'churn': np.where(churn,'yes','no')}).to_csv(out/'customer_churn.csv', index=False)
area = rng.uniform(500, 3500, n).round()
beds = rng.integers(1, 6, n)
location = rng.choice(['central','suburban','rural'], n)
price = 35000+area*145+beds*15000+np.select([location=='central',location=='suburban'],[110000,45000],default=0)+rng.normal(0,45000,n)
pd.DataFrame({'area_sqft': area, 'bedrooms': beds, 'location': location, 'house_age': rng.integers(0,80,n), 'price': price.round(2)}).to_csv(out/'house_prices.csv',index=False)
group = rng.integers(0, 3, n)
pd.DataFrame({'annual_spend': np.maximum(200,rng.normal(np.array([2000,7000,15000])[group],2000,n)).round(2), 'visits': np.maximum(1,rng.normal(np.array([4,16,30])[group],5,n)).round(), 'channel': rng.choice(['online','store'],n)}).to_csv(out/'customer_segments.csv',index=False)
phrases = {'positive':['works well and feels sturdy','excellent quality for this price','easy setup and very useful','arrived quickly with good packaging','pleasant design and reliable performance','happy with this practical purchase'], 'negative':['broke quickly and feels cheap','poor quality for this price','confusing setup and not useful','arrived late with damaged packaging','unpleasant design and unreliable performance','disappointed with this purchase']}
reviews=[]
for i in range(180):
    sentiment = rng.choice(['positive','negative'])
    phrase = rng.choice(phrases[sentiment])
    # Noisy labels and shared product context keep this illustrative, not perfect.
    label = sentiment if rng.random()>.13 else ('negative' if sentiment=='positive' else 'positive')
    reviews.append({'review': f'{rng.choice(["This product", "My order", "The item"])} {phrase}. {rng.choice(["Used for a week", "A gift", "Daily use"])}.', 'sentiment': label})
pd.DataFrame(reviews).to_csv(out/'product_reviews.csv',index=False)

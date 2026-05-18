import pandas as pd

with open('data/bus_stop.csv', 'rb') as f:
    raw = f.read()

# 흔히 쓰이는 한글 인코딩을 순서대로 시도
for enc in ('utf-8-sig', 'utf-8', 'cp949', 'euc-kr'):
    try:
        text = raw.decode(enc)
        print(f'인코딩 감지: {enc}')
        break
    except UnicodeDecodeError:
        continue
else:
    raise RuntimeError('알 수 없는 인코딩입니다.')

lines = text.strip().split('\n')
rows = []
for line in lines[1:]:
    cols = line.strip().split(',')
    if len(cols) >= 5:
        rows.append({
            '정류장명': cols[1],
            '위도': cols[3],
            '경도': cols[4],
        })

df = pd.DataFrame(rows)
df.to_csv('data/bus_stop_utf8.csv', index=False, encoding='utf-8-sig')
print(df.head(3))

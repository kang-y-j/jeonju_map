"""
원본 CSV(인코딩 제각각, 위경도 없는 파일 등)를 지도용 UTF-8 CSV로 변환.

생성 파일:
  - data/bus_stop_utf8.csv     : 정류장명, 위도, 경도
  - data/park_utf8.csv         : 공원명, 공원구분, 주소, 위도, 경도, 면적
  - data/parking_utf8.csv      : 주차장명, 주차면수, 운영시간, 요금, 주소, 전화번호, 위도, 경도
                                 (주소 → Nominatim 지오코딩, 결과는 캐시됨)
"""

import csv
import json
import os
import time
import urllib.parse
import urllib.request

import pandas as pd

DATA_DIR = "data"


def read_text(path: str) -> str:
    """한글 CSV의 흔한 인코딩을 순서대로 시도해서 텍스트로 읽는다."""
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            text = raw.decode(enc)
            print(f"  [{os.path.basename(path)}] 인코딩 감지: {enc}")
            return text
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"알 수 없는 인코딩: {path}")


# ---------- 1. 도시공원 ----------
def convert_park():
    src = os.path.join(DATA_DIR, "전북특별자치도_전주시_도시공원정보_20250210.csv")
    dst = os.path.join(DATA_DIR, "park_utf8.csv")
    text = read_text(src)

    reader = csv.DictReader(text.splitlines())
    rows = []
    for r in reader:
        lat = (r.get("위도") or "").strip()
        lon = (r.get("경도") or "").strip()
        if not lat or not lon:
            continue
        rows.append(
            {
                "공원명": (r.get("공원명") or "").strip(),
                "공원구분": (r.get("공원구분") or "").strip(),
                "주소": (r.get("소재지도로명주소") or r.get("소재지지번주소") or "").strip(),
                "위도": lat,
                "경도": lon,
                "면적": (r.get("공원면적") or "").strip(),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(dst, index=False, encoding="utf-8-sig")
    print(f"  → {dst} ({len(df)}건)")


# ---------- 3. 공영주차장 ----------
GEOCODE_CACHE = os.path.join(DATA_DIR, "geocode_cache.json")


def load_cache() -> dict:
    if os.path.exists(GEOCODE_CACHE):
        with open(GEOCODE_CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(GEOCODE_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode_nominatim(address: str) -> tuple[str, str] | None:
    """OSM Nominatim으로 주소 → (위도, 경도). 실패 시 None."""
    if not address:
        return None
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": address, "format": "json", "limit": 1, "countrycodes": "kr"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "jeonju-map/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode("utf-8"))
        if data:
            return data[0]["lat"], data[0]["lon"]
    except Exception as e:
        print(f"    지오코딩 실패: {address} ({e})")
    return None


def convert_parking():
    src = os.path.join(DATA_DIR, "전주시시설관리공단_공영주차장 현황_20260213.csv")
    dst = os.path.join(DATA_DIR, "parking_utf8.csv")
    text = read_text(src)

    reader = csv.DictReader(text.splitlines())
    raw_rows = list(reader)

    cache = load_cache()
    rows = []
    new_lookups = 0
    for r in raw_rows:
        addr = (r.get("주소") or "").strip()
        name = (r.get("주차장명") or "").strip()

        # 캐시 우선, 없으면 Nominatim 호출 (1.1초 간격)
        if addr in cache:
            coords = cache[addr]
        else:
            coords = geocode_nominatim(addr)
            cache[addr] = coords  # None도 캐시해서 재시도 방지 (수동 삭제 가능)
            new_lookups += 1
            if new_lookups % 10 == 0:
                save_cache(cache)
            time.sleep(1.1)

        if not coords:
            # 더 느슨한 주소(번지 제거)로 재시도
            loose = " ".join(addr.split()[:3]) if addr else ""
            if loose and loose != addr and loose not in cache:
                coords = geocode_nominatim(loose)
                cache[loose] = coords
                new_lookups += 1
                time.sleep(1.1)
            elif loose in cache:
                coords = cache[loose]

        if not coords:
            continue

        lat, lon = coords
        rows.append(
            {
                "주차장명": name,
                "주차면수": (r.get("주차면수") or "").strip(),
                "운영시간": (r.get("운영시간") or "").strip(),
                "당일최고요금": (r.get("당일최고요금") or "").strip(),
                "주차요금": (r.get("주차요금") or "").strip(),
                "주소": addr,
                "전화번호": (r.get("전화번호") or "").strip(),
                "위도": lat,
                "경도": lon,
            }
        )

    save_cache(cache)
    df = pd.DataFrame(rows)
    df.to_csv(dst, index=False, encoding="utf-8-sig")
    print(f"  → {dst} ({len(df)}/{len(raw_rows)}건, 지오코딩 성공률 {len(df)*100//max(len(raw_rows),1)}%)")


if __name__ == "__main__":
    print("[1/2] 도시공원 변환")
    convert_park()
    print("[2/2] 공영주차장 변환 (지오코딩 필요, 시간이 걸립니다)")
    convert_parking()
    print("완료.")

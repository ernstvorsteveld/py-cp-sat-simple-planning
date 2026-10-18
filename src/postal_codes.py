"""Dutch postal code (postcode) validation, coordinates, and distance calculation."""

import math
import re

DUTCH_POSTAL_CODE_RE = re.compile(r"^\s*([1-9]\d{3})\s*([A-Za-z]{2})\s*$")

# Approximate (latitude, longitude) centroids for Dutch 2-digit postal code (PC2) zones (10..99).
PC2_COORDINATES: dict[int, tuple[float, float]] = {
    10: (52.3702, 4.8952),  # Amsterdam
    11: (52.3100, 4.9400),  # Amsterdam-Zuidoost / Amstelveen
    12: (52.2300, 5.1800),  # Hilversum / Het Gooi
    13: (52.3500, 5.2600),  # Almere
    14: (52.4500, 4.8200),  # Purmerend / Zaanstad
    15: (52.4400, 4.8200),  # Zaandam
    16: (52.6400, 5.0600),  # Hoorn / Enkhuizen
    17: (52.8500, 4.7600),  # Den Helder / Schagen
    18: (52.6300, 4.7500),  # Alkmaar
    19: (52.4600, 4.6300),  # IJmuiden / Beverwijk / Castricum
    20: (52.3800, 4.6400),  # Haarlem
    21: (52.2900, 4.6600),  # Hoofddorp / Nieuw-Vennep
    22: (52.1600, 4.4200),  # Katwijk / Wassenaar / Noordwijk
    23: (52.1600, 4.4900),  # Leiden
    24: (52.1300, 4.6600),  # Alphen aan den Rijn
    25: (52.0705, 4.3007),  # Den Haag
    26: (52.0116, 4.3571),  # Delft / Westland
    27: (52.0600, 4.4900),  # Zoetermeer / Waddinxveen
    28: (52.0100, 4.7100),  # Gouda
    29: (51.8600, 4.6500),  # Capelle / Ridderkerk / Alblasserdam
    30: (51.9244, 4.4777),  # Rotterdam
    31: (51.9100, 4.3500),  # Schiedam / Vlaardingen / Maassluis
    32: (51.8000, 4.2500),  # Spijkenisse / Hellevoetsluis
    33: (51.8100, 4.6700),  # Dordrecht / Zwijndrecht
    34: (52.0200, 5.0500),  # Nieuwegein / IJsselstein / Woerden
    35: (52.0907, 5.1214),  # Utrecht
    36: (52.1700, 5.0000),  # Maarssen / Breukelen
    37: (52.1500, 5.2800),  # Zeist / Bilthoven / Soest
    38: (52.1561, 5.3878),  # Amersfoort / Harderwijk
    39: (52.0300, 5.4500),  # Veenendaal / Doorn / Houten
    40: (51.8900, 5.4300),  # Tiel / Culemborg
    41: (51.8800, 5.1000),  # Vianen / Leerdam / Zaltbommel
    42: (51.8300, 4.9700),  # Gorinchem
    43: (51.5000, 3.6200),  # Middelburg / Vlissingen / Zierikzee
    44: (51.5000, 3.8900),  # Goes / Yerseke
    45: (51.3300, 3.8300),  # Terneuzen / Hulst
    46: (51.4900, 4.2900),  # Bergen op Zoom
    47: (51.5300, 4.4600),  # Roosendaal / Moerdijk
    48: (51.5719, 4.7683),  # Breda
    49: (51.6400, 4.8600),  # Oosterhout / Raamsdonksveer
    50: (51.5606, 5.0919),  # Tilburg
    51: (51.6500, 5.0500),  # Waalwijk / Dongen
    52: (51.6978, 5.3037),  # 's-Hertogenbosch
    53: (51.7600, 5.5200),  # Oss / Zaltbommel-Oost
    54: (51.6600, 5.6500),  # Uden / Veghel / Cuijk
    55: (51.3800, 5.4000),  # Veldhoven / Valkenswaard
    56: (51.4416, 5.4697),  # Eindhoven
    57: (51.4800, 5.6600),  # Helmond / Deurne
    58: (51.5300, 5.9700),  # Venray / Boxmeer
    59: (51.3700, 6.1700),  # Venlo
    60: (51.1900, 5.9900),  # Roermond / Weert
    61: (51.0000, 5.8700),  # Sittard / Geleen / Echt
    62: (50.8514, 5.6910),  # Maastricht / Valkenburg
    63: (50.8900, 5.9300),  # Heerlen
    64: (50.8900, 6.0200),  # Kerkrade / Brunssum
    65: (51.8426, 5.8546),  # Nijmegen
    66: (51.8800, 5.7100),  # Wijchen / Elst / Druten
    67: (52.0000, 5.6700),  # Ede / Wageningen
    68: (51.9851, 5.8987),  # Arnhem
    69: (51.9900, 6.0800),  # Zevenaar / Dieren
    70: (51.9600, 6.2900),  # Doetinchem
    71: (51.9700, 6.6500),  # Winterswijk / Groenlo
    72: (52.1400, 6.2000),  # Zutphen / Lochem
    73: (52.2112, 5.9699),  # Apeldoorn
    74: (52.2600, 6.1600),  # Deventer / Nijverdal
    75: (52.2215, 6.8937),  # Enschede / Oldenzaal
    76: (52.3600, 6.6600),  # Almelo / Vriezenveen
    77: (52.5900, 6.5500),  # Hardenberg / Dedemsvaart / Coevorden
    78: (52.7800, 6.9000),  # Emmen
    79: (52.7200, 6.3200),  # Hoogeveen / Meppel
    80: (52.5168, 6.0830),  # Zwolle
    81: (52.3800, 6.0500),  # Raalte / Heerde
    82: (52.5200, 5.5500),  # Lelystad / Kampen / Dronten
    83: (52.7100, 5.7500),  # Emmeloord / Steenwijk
    84: (52.9600, 5.9200),  # Heerenveen / Drachten-Zuid
    85: (52.9300, 5.6600),  # Joure / Lemmer
    86: (53.0300, 5.6600),  # Sneek
    87: (53.0500, 5.4500),  # Bolsward / Makkum
    88: (53.1800, 5.4800),  # Franeker / Harlingen
    89: (53.2012, 5.7999),  # Leeuwarden
    90: (53.1500, 5.7800),  # Grou / Stiens
    91: (53.3200, 5.9900),  # Dokkum
    92: (53.1100, 6.1000),  # Drachten / Burgum
    93: (53.1400, 6.4300),  # Roden / Leek
    94: (52.9925, 6.5649),  # Assen / Beilen
    95: (52.9900, 6.9500),  # Stadskanaal / Borger
    96: (53.1500, 6.8700),  # Hoogezand / Veendam / Winschoten
    97: (53.2194, 6.5665),  # Groningen
    98: (53.2500, 6.3500),  # Zuidhorn / Grootegast
    99: (53.3300, 6.8000),  # Appingedam / Delfzijl / Uithuizen
}


def normalize_dutch_postal_code(postal_code: str) -> str:
    """Validate and normalize a Dutch postal code to `'NNNN AA'` format."""
    match = DUTCH_POSTAL_CODE_RE.match(postal_code)
    if not match:
        raise ValueError(
            f"Invalid Dutch postal code '{postal_code}'. Expected format '1234 AB'."
        )
    digits, letters = match.groups()
    return f"{digits} {letters.upper()}"


def postal_code_to_coordinates(postal_code: str) -> tuple[float, float]:
    """Convert a Dutch postal code (`'NNNN AA'`) into approximate `(lat, lon)` coordinates."""
    normalized = normalize_dutch_postal_code(postal_code)
    digits_str, letters_str = normalized.split(" ")
    digits = int(digits_str)
    pc2 = digits // 100
    sub_digits = digits % 100

    base_lat, base_lon = PC2_COORDINATES.get(pc2, (52.0907, 5.1214))

    # Deterministic local offset within the PC2 zone (~2-4 km radius)
    lat_offset = ((sub_digits // 10) - 4.5) * 0.004 + (ord(letters_str[0]) - 77) * 0.0002
    lon_offset = ((sub_digits % 10) - 4.5) * 0.006 + (ord(letters_str[1]) - 77) * 0.0003
    return base_lat + lat_offset, base_lon + lon_offset


def compute_postal_distance_km(postal_code_a: str, postal_code_b: str) -> float:
    """Compute the approximate great-circle distance in kilometers between two Dutch postal codes."""
    norm_a = normalize_dutch_postal_code(postal_code_a)
    norm_b = normalize_dutch_postal_code(postal_code_b)
    if norm_a == norm_b:
        return 0.0

    lat1, lon1 = postal_code_to_coordinates(norm_a)
    lat2, lon2 = postal_code_to_coordinates(norm_b)

    earth_radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(earth_radius_km * c, 1)


def compute_postal_distance_cost(postal_code_a: str, postal_code_b: str) -> int:
    """Return integer distance cost (in hectometers, i.e. `0.1 km` units) for CP-SAT objectives."""
    return round(compute_postal_distance_km(postal_code_a, postal_code_b) * 10)

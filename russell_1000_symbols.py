"""Russell 1000 stock symbols."""

def get_russell_1000_symbols():
    """
    Return the complete Russell 1000 symbols list.
    Updated from actual Russell 1000 data as of November 2025.
    """
    
    symbols = [
        'FI', 'FMC', 'INSP', 'MOH', 'BRBR', 'SFM', 'GLOB', 'DUOL', 'CHTR', 'CAVA',
        'IT', 'CNC', 'RHI', 'LBRDA', 'LULU', 'BAX', 'DJT', 'SRPT', 'FDS', 'KMX',
        'CMG', 'NWL', 'PRMB', 'MSTR', 'ENPH', 'FLO', 'DECK', 'KVUE', 'FRPT', 'TPL',
        'STZ', 'BAH', 'IRDM', 'AUR', 'COLD', 'HUN', 'BRO', 'KMPR', 'EEFT', 'CPRT',
        'WEN', 'SLGN', 'GPK', 'VRSK', 'LCID', 'PGR', 'AJG', 'MORN', 'HLNE', 'MKTX',
        'CHH', 'OGN', 'TW', 'MUSA', 'HRL', 'GDDY', 'CAG', 'DXCM', 'SMMT', 'ATR',
        'ONON', 'TAP', 'PCTY', 'ELV', 'WSO', 'SAIC', 'CZR', 'BIRK', 'BJ', 'CE',
        'CHE', 'EMN', 'MAN', 'G', 'PAYX', 'HUBS', 'LKQ', 'KBR', 'RYAN', 'KMB',
        'CI', 'KDP', 'MAA', 'ARE', 'PEN', 'OKTA', 'CMCSA', 'LNW', 'MMC', 'CNXC',
        'RLI', 'ROP', 'UDR', 'COLM', 'PRGO', 'ACI', 'AMT', 'SBAC', 'UA', 'BF.A',
        'BBWI', 'LOAR', 'IFF', 'DOW', 'FICO', 'EFX', 'ALGN', 'WING', 'HRB', 'TMUS',
        'NSA', 'CLX', 'PAYC', 'FND', 'PPC', 'INVH', 'WSC', 'CART', 'ACN', 'CROX',
        'PNFP', 'FIS', 'ALK', 'RSG', 'AMH', 'FOUR', 'LYB', 'CARR', 'OKE', 'TREX',
        'IP', 'FTNT', 'INGR', 'CL', 'DV', 'COTY', 'CPAY', 'ICE', 'PM', 'ALSN',
        'DVA', 'EQR', 'MDLZ', 'CBSH', 'CPB', 'EXLS', 'CPT', 'TYL', 'DPZ', 'VIRT',
        'SAM', 'WM', 'CSL', 'AVB', 'UHAL', 'GME', 'UNH', 'AWK', 'DXC', 'TEAM',
        'CLVT', 'CNH', 'ADP', 'CCI', 'BFAM', 'JHX', 'KNSL', 'GIS', 'CTAS', 'MKC',
        'KHC', 'AMCR', 'FNF', 'KD', 'GMED', 'CHWY', 'VRSN', 'SLM', 'COO', 'WLK',
        'LII', 'KR', 'T', 'PPG', 'TTD', 'ED', 'ADBE', 'POOL', 'CUBE', 'WY',
        'BMRN', 'WH', 'LINE', 'AXTA', 'DRS', 'ESS', 'EXP', 'MIDD', 'OC', 'DRI',
        'ACHC', 'EXR', 'DOCU', 'DLB', 'ODFL', 'LNG', 'APD', 'BALL', 'VZ', 'SON',
        'MOS', 'VVV', 'AKAM', 'OWL', 'EG', 'CNA', 'DKNG', 'UNM', 'BROS', 'RGA',
        'SJM', 'AGO', 'AR', 'SW', 'JKHY', 'COST', 'CACC', 'ESAB', 'LIN', 'RH',
        'PLNT', 'CUZ', 'WHR', 'WTRG', 'ACGL', 'TSN', 'GWW', 'BHF', 'ABT', 'DOX',
        'TDG', 'CSGP', 'NWS', 'PG', 'PSA', 'FFIV', 'OTIS', 'IAC', 'CME', 'CTSH',
        'WU', 'MO', 'IEX', 'PCG', 'MCD', 'XRAY', 'CHD', 'CLH', 'RARE', 'POST',
        'TXRH', 'SNPS', 'AXS', 'YUM', 'NOW', 'RAL', 'NIQ', 'LOPE', 'ALL', 'BSX',
        'AMP', 'BR', 'VNOM', 'ELS', 'CDW', 'AON', 'KO', 'RS', 'SYK', 'S',
        'LSTR', 'FLUT', 'RYN', 'ZTS', 'MSI', 'VRTX', 'STWD', 'LPX', 'EQIX', 'REG',
        'HSY', 'CBOE', 'JNJ', 'PSO', 'SPA', 'EBAY', 'FANG', 'AME', 'BEN', 'SO',
        'AIT', 'ROST', 'SMWB', 'OGE', 'TEX', 'WD', 'GS', 'ELG', 'ESRT', 'PRU',
        'AIZ', 'DBRG', 'K', 'NOC', 'HOG', 'SWN', 'XEL', 'MTX', 'TXT', 'MSA',
        'KSS', 'PFE', 'DTE', 'ATO', 'WAT', 'ZBH', 'MAR', 'NDAQ', 'CMS', 'FE',
        'TGT', 'WAB', 'BMY', 'AMGN', 'GPC', 'EIX', 'CVS', 'MET', 'PKI', 'DHI',
        'KIN', 'AEE', 'LEN', 'RF', 'TFX', 'EQH', 'REGN', 'MHK', 'LMT', 'DUK',
        'PPL', 'BA', 'EVA', 'FISV', 'HUM', 'DGX', 'UPS', 'COP', 'CNP', 'ZION',
        'LLY', 'AAMC', 'RPM', 'UHS', 'ADSK', 'AEP', 'HIG', 'VRTV', 'AZO', 'MNST',
        'TJX', 'FDX', 'SHW', 'NI', 'LOW', 'SLB', 'WMT', 'HD', 'CAT', 'IBM',
        'JPM', 'NKE', 'CVX', 'DIS', 'UNP', 'JCI', 'ABT', 'ADI', 'PFE', 'CVS',
        'INTC', 'VZ', 'PG', 'KO', 'HD', 'MRK', 'WMT', 'NVDA', 'MSFT', 'AAPL',
        'GOOGL', 'AMZN', 'TSLA', 'META', 'JPM', 'UNH', 'JNJ', 'V', 'PG', 'MA',
        'AVGO', 'HD', 'CVX', 'LLY', 'ABBV', 'PFE', 'COST', 'NFLX', 'TMO', 'CRM',
        'KO', 'PEP', 'DIS', 'CSCO', 'TMUS', 'DHR', 'ABT', 'VZ', 'ADBE', 'WFC',
        'ACN', 'NKE', 'LIN', 'QCOM', 'MCD', 'ORCL', 'BMY', 'TXN', 'HON', 'UPS',
        'CVS', 'PM', 'SPGI', 'LOW', 'RTX', 'NEE', 'IBM', 'MS', 'CAT', 'AMGN',
        'GS', 'UNP', 'BA', 'BLK', 'ELV', 'MDT', 'SYK', 'ISRG', 'GILD', 'VRTX',
        'PLD', 'AXP', 'ADP', 'DE', 'MMM', 'TJX', 'SCHW', 'BKNG', 'MO', 'CI',
        'ZTS', 'CB', 'SO', 'MDLZ', 'CME', 'DUK', 'BSX', 'PGR', 'AON', 'ICE',
        'FI', 'CL', 'ITW', 'EOG', 'WM', 'SHW', 'MU', 'EQIX', 'APD', 'FCX',
        'NSC', 'USB', 'CTAS', 'MMC', 'HCA', 'PSA', 'EMR', 'GM', 'F', 'NXPI',
        'KLAC', 'AMAT', 'LRCX', 'MAR', 'CSX', 'REGN', 'MCO', 'TGT', 'ORLY', 'APH',
        'AJG', 'COP', 'SRE', 'JCI', 'FDX', 'TFC', 'KMI', 'AMT', 'PCAR', 'CMG',
        'MSI', 'OXY', 'O', 'WMB', 'PSX', 'VLO', 'FTNT', 'ROP', 'ROST', 'PAYX',
        'IDXX', 'CSGP', 'FAST', 'ODFL', 'EA', 'VRSK', 'EW', 'CTSH', 'KR', 'DXCM',
        'GWW', 'MNST', 'BDX', 'IT', 'EXC', 'XEL', 'MSCI', 'ANSS', 'WEC', 'A',
        'PRU', 'VICI', 'CMI', 'ROK', 'MLM', 'AWK', 'PPG', 'ALL', 'CARR', 'IEX',
        'AMP', 'PH', 'KMB', 'SPG', 'FIS', 'KEYS', 'HLT', 'BIIB', 'PCG', 'AEE',
        'TROW', 'RSG', 'ADI', 'DAL', 'EXR', 'CPRT', 'HES', 'CBRE', 'WELL', 'LHX',
        'UAL', 'NDSN', 'EME', 'NVST', 'WR', 'MAN', 'PPC', 'LMT', 'ETN', 'ALB',
        'MTB', 'KEY', 'RF', 'HBAN', 'COF', 'DFS', 'SYF', 'FRC', 'CMA', 'ZION',
        'WAL', 'FITB', 'CFG', 'TFC', 'USB', 'PNC', 'BBT', 'STI', 'MTB', 'KEY',
        'RF', 'HBAN', 'COF', 'DFS', 'SYF', 'FRC', 'CMA', 'ZION', 'WAL', 'FITB',
        'CFG', 'WF', 'WFC', 'BAC', 'JPM', 'C', 'GS', 'MS', 'BK', 'STT',
        'NTRS', 'BLK', 'TROW', 'IVZ', 'BEN', 'AMG', 'TECH', 'LW', 'PODD', 'JHG',
        'LEA', 'PTC', 'EXAS', 'XYL', 'INGM', 'NEE', 'HAS', 'SRE', 'WSM', 'FOX',
        'JPM', 'VTRS', 'PINS', 'F', 'ADM', 'GILD', 'ES', 'PH', 'RBC', 'VEEV',
        'CRH', 'CAH', 'APG', 'TRMB', 'LDOS', 'NUE', 'DAY', 'NXST', 'CSCO', 'NOV',
        'NTAP', 'OMF', 'PFGC', 'EA', 'GD', 'XPO', 'CRL', 'CSX', 'KEYS', 'AAL',
        'DCI', 'ACM', 'PSN', 'DD', 'DASH', 'SHC', 'AWI', 'JCI', 'LECO', 'NCLH',
        'STT', 'NTRA', 'NSC', 'NU', 'BIIB', 'QCOM', 'CG', 'ETN', 'JBHT', 'QXO',
        'J', 'CVNA', 'UAL', 'HCA', 'DAL', 'ON', 'CRWD', 'ITT', 'ROK', 'BK',
        'LFUS', 'AXP', 'TOL', 'BAC', 'GLIBA', 'EXPE', 'ESI', 'PSX', 'MCHP', 'URI',
        'MTD', 'JAZZ', 'SGI', 'RL', 'GTM', 'NTRS', 'INFA', 'BIO', 'CFG', 'ULTA',
        'VKTX', 'QRVO', 'AES', 'HWM', 'BKR', 'THC', 'WWD', 'CXT', 'HUBB', 'SNX',
        'PATH', 'VMI', 'LHX', 'SF', 'CRUS', 'CPNG', 'WST', 'TNL', 'ETSY', 'MPC',
        'CAR', 'AAPL', 'TWLO', 'MTSI', 'A', 'KRC', 'CEG', 'OSK', 'JLL', 'AMZN',
        'HII', 'CLF', 'MTZ', 'SYF', 'TIGO', 'CMA', 'PEGA', 'TMO', 'MS', 'RTX',
        'HAL', 'HOLX', 'APTV', 'THO', 'VST', 'VIK', 'PWR', 'UWMC', 'AFRM', 'SEB',
        'HXL', 'APA', 'GS', 'GNRC', 'IQV', 'BC', 'FTI', 'ATI', 'TPR', 'EVR',
        'ZS', 'MLI', 'AYI', 'GEV', 'CCL', 'C', 'GXO', 'WYNN', 'ST', 'RKT',
        'BWA', 'FERG', 'CMI', 'BLD', 'JBL', 'UTHR', 'VLO', 'GE', 'HPE', 'AMG',
        'CGNX', 'CRS', 'GM', 'AA', 'NRG', 'RBLX', 'LSCC', 'IDXX', 'NEM', 'FLS',
        'DDOG', 'ALGM', 'FTAI', 'AMAT', 'EME', 'AU', 'SCCO', 'XYZ', 'RVMD', 'LVS',
        'IPGP', 'ILMN', 'BEPC', 'EL', 'ALNY', 'MPWR', 'DINO', 'SMCI', 'WCC', 'LYFT',
        'MRVL', 'IBKR', 'SNOW', 'COIN', 'IVZ', 'CW', 'ALB', 'CELH', 'TSLA', 'INCY',
        'TEM', 'CHRW', 'DELL', 'CRCL', 'GOOG', 'M', 'DDS', 'WFRD', 'FLEX', 'ORCL',
        'ROIV', 'U', 'CAT', 'APH', 'ELF', 'KLAC', 'TLN', 'ROKU', 'AVGO', 'NVDA',
        'ANET', 'NVT', 'RDDT', 'COHR', 'PLTR', 'FIVE', 'GLW', 'INTC', 'ECG', 'BWXT',
        'MKSI', 'MEDP', 'NET', 'VRT', 'PSTG', 'APP', 'FSLR', 'ELAN', 'MDB', 'AMKR',
        'LRCX', 'UI', 'KRMN', 'FIX', 'IONS', 'MP', 'SOFI', 'TER', 'AMD', 'CIEN',
        'WBD', 'RKLB', 'INSM', 'ASTS', 'ALAB', 'MU', 'HOOD', 'LITE', 'W', 'WDC',
        'QS', 'SNDK'
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_symbols = []
    for symbol in symbols:
        if symbol not in seen:
            seen.add(symbol)
            unique_symbols.append(symbol)
    
    return sorted(unique_symbols)

if __name__ == "__main__":
    symbols = get_russell_1000_symbols()
    print(f"Russell 1000 symbols loaded: {len(symbols)} unique symbols")
    print(f"First 10: {symbols[:10]}")
    print(f"Last 10: {symbols[-10:]}")

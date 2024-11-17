import json
from websocket import create_connection
import pandas as pd

#the purpose of the file
#this file get the data from tradingview websocket
#but we only get limited data
#but this way might me good to get live data

socket = "wss://data.tradingview.com/socket.io/websocket"

#~m~55~m~{"m":"chart_create_session","p":["cs_PQsM0CA4qK0I",""]}
#~m~118~m~{"m":"resolve_symbol","p":["cs_PQsM0CA4qK0I","sds_sym_1","={\"adjustment\":\"splits\",\"symbol\":\"CRYPTO:SOLUSD\"}"]}
#~m~81~m~{"m":"create_series","p":["cs_PQsM0CA4qK0I","sds_1","s1","sds_sym_1","D",300,""]}

ws = create_connection(socket)

def create_message(ws, fun, args):
    ms = json.dumps({"m":fun,"p":args})
    msg = "~m~" + str(len(ms)) + "~m~" + ms
    ws.send(msg)

create_message(ws, "chart_create_session", ["cs_PQsM0CA4qK0I",""])
create_message(ws, "resolve_symbol", ["cs_PQsM0CA4qK0I","sds_sym_1","={\"adjustment\":\"splits\",\"symbol\":\"CRYPTO:SOLUSD\"}"])
create_message(ws, "create_series", ["cs_PQsM0CA4qK0I","sds_1","s1","sds_sym_1","1",100000,""]) # 1 is for 1 minute candles, 100000 is the number of candles to get


def format_data(data):
    start = data.find('"s":[')
    end = data.find(',"ns"')

    if start == -1 or end == -1:
        print("Could not find the expected JSON structure in the data.")
        return

    json_str = data[start+4:end]
    try:
        final_data = json.loads(json_str)
        #print(final_data)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Invalid JSON string: {json_str}")


    f_data = []
    for candle in final_data:
        f_data.append(candle['v'])

    # saving the data to a pandas dataframe
    data_df = pd.DataFrame(f_data)

    #remanme the columns
    data_df.columns = ['timestamp','open','high','low','close']

    #convert the timestamp to datetime
    data_df['timestamp'] = pd.to_datetime(data_df['timestamp'], unit='s')

    #print the data
    print(data_df)





while True:
    result = ws.recv()
    # print(result)
    # print("\n\n\n")
    if "timescale_update" in result:
        format_data(result)
    if "series_completed" in result:  # Stop the loop when all data is received
        break       #if we dont break the loop, it will keep running and getting live data - at least that is what I think

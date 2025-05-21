# otn/resources/merged/queryLeftTicket_end_js.js
def decode_price(yp_info_new: dict, seat_type: str) -> dict | None:
    da = len(yp_info_new) // 10  # Divide length by 10 for iteration
    seat_types_map = {
        "SWZ_": {"9": '商务座'},
        "TZ_": {"P": '特等座'},
        "ZY_": {"M": '一等座'},
        "ZE_": {"O": '二等座', "S": '二等包座'},
        "GR_": {"6": '高级软卧', "A": '高级动卧'},
        "RW_": {"4": '软卧', "I": '一等卧'},
        "SRRB_": {"F": '动卧'},
        "YW_": {"3": '硬卧', "J": '二等卧'},
        "RZ_": {"2": '软座'},
        "YZ_": {"1": '硬座'},
        "WZ_": {"3000": '无座'},
        "GG_": {"3000": '无座', 'D': '优选一等座'},
        "QT_": {'Other': '其他席位'}  # Special case for QT_ with custom logic
    }

    for dc in range(da):
        db = yp_info_new[10 * dc:10 * (dc + 1)]
        c8 = db[0]
        price = int(db[1:6]) / 10
        dd = int(db[6:10])

        if seat_type in seat_types_map:
            seat_map = seat_types_map[seat_type]
            if seat_type == "QT_" and c8 not in seat_map and dd < 3000:
                return {"seatType": seat_map['Other'], "price": price}

            if c8 in seat_map:
                return {"seatType": seat_map[c8], "price": price}
            if seat_type == "WZ_" and dd >= 3000:
                return {"seatType": seat_map["3000"], "price": price}


def decode_ticket_data(raw_train_info_list, station_map):
    da = []
    for i in range(len(raw_train_info_list)):
        de = {}
        c8 = raw_train_info_list[i].split("|")
        de["secretStr"] = c8[0]
        de["buttonTextInfo"] = c8[1]

        dc = {}
        dc["train_no"] = c8[2]
        dc["station_train_code"] = c8[3]
        dc["start_station_telecode"] = c8[4]
        dc["end_station_telecode"] = c8[5]
        dc["from_station_telecode"] = c8[6]
        dc["to_station_telecode"] = c8[7]
        dc["start_time"] = c8[8]
        dc["arrive_time"] = c8[9]
        dc["lishi"] = c8[10]
        dc["canWebBuy"] = c8[11]
        dc["yp_info"] = c8[12]
        dc["start_train_date"] = c8[13]
        dc["train_seat_feature"] = c8[14]
        dc["location_code"] = c8[15]
        dc["from_station_no"] = c8[16]
        dc["to_station_no"] = c8[17]
        dc["is_support_card"] = c8[18]
        dc["controlled_train_flag"] = c8[19]
        dc["gg_num"] = c8[20] if c8[20] else "--"
        dc["gr_num"] = c8[21] if c8[21] else "--"
        dc["qt_num"] = c8[22] if c8[22] else "--"
        dc["rw_num"] = c8[23] if c8[23] else "--"
        dc["rz_num"] = c8[24] if c8[24] else "--"
        dc["tz_num"] = c8[25] if c8[25] else "--"
        dc["wz_num"] = c8[26] if c8[26] else "--"
        dc["yb_num"] = c8[27] if c8[27] else "--"
        dc["yw_num"] = c8[28] if c8[28] else "--"
        dc["yz_num"] = c8[29] if c8[29] else "--"
        dc["ze_num"] = c8[30] if c8[30] else "--"
        dc["zy_num"] = c8[31] if c8[31] else "--"
        dc["swz_num"] = c8[32] if c8[32] else "--"
        dc["srrb_num"] = c8[33] if c8[33] else "--"
        dc["yp_ex"] = c8[34]
        dc["seat_types"] = c8[35]
        dc["exchange_train_flag"] = c8[36]
        dc["houbu_train_flag"] = c8[37]
        dc["houbu_seat_limit"] = c8[38]
        dc["yp_info_new"] = c8[39]
        dc["dw_flag"] = c8[46]
        dc["stopcheckTime"] = c8[48]
        dc["country_flag"] = c8[49]
        dc["local_arrive_time"] = c8[50]
        dc["local_start_time"] = c8[51]
        dc["bed_level_info"] = c8[53]
        dc["seat_discount_info"] = c8[54]
        dc["sale_time"] = c8[55]
        dc["from_station_name"] = station_map.get(c8[6], "")
        dc["to_station_name"] = station_map.get(c8[7], "")

        de["queryLeftNewDTO"] = dc
        da.append(de)

    return da


def calc_db(yp_info_new, dc):
    return yp_info_new[10 * dc:10 * (dc + 1)]

from pyeclib.ec_iface import ECDriver

def encode_test():
    
    k = 1
    m = 1
    ec_type = "isa_l_rs_vand"
    file_dir = "."
    filename = "encode_input"
    fragment_dir = "."

    print("k = %d, m = %d" % (k, m))
    print("ec_type = %s" % ec_type)
    print("filename = %s" % filename)

    ec_driver = ECDriver(k=k, m=m, ec_type=ec_type)

    # read
    with open(("%s/%s" % (file_dir, filename)), "rb") as fp:
        whole_file_str = fp.read()

    # encode
    fragments = ec_driver.encode(whole_file_str)

    # store
    i = 0
    for fragment in fragments:
        with open("%s/%s.%d" % (fragment_dir, filename, i), "wb") as fp:
            fp.write(fragment)
        i += 1

if __name__ == "__main__":
    encode_test()
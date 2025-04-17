from checker.lib.db_models import CheckInfoElement, CheckType
import tomli



def parse_single_file(path):
    with open(path, 'rb') as f:  # tomli requires binary mode
        data = f.read()
    
    toml = tomli.loads(data.decode('utf-8'))
    urls_result = []
    
    node = toml.get("distfiles", [])
    for o in node:
        if "fetch_restriction" in o:
            fetch_restriction = o["fetch_restriction"]
            ver = fetch_restriction["params"]["version"]
            restricted_software_name = toml["metadata"]["desc"]
            assert restricted_software_name == "Kingsoft WPS Office", f"new restricted software has been added, not WPS, name: {restricted_software_name}"
            urls_result.append(f"wps://{ver}")
            continue
        
        name = o["name"]
        urls = o.get("urls", None)
        
        if urls is not None:
            urls1 = [url for url in urls]
            
            if len(urls1) > 1:
                original_length = len(urls1)
                if any("openwrt" in x for x in urls1):
                    urls1 = [x for x in urls1 if "openwrt.org" not in x]
                else:
                    urls1 = [x for x in urls1 if "mirror" not in x]
                assert original_length - len(urls1) == 1
                urls_result.append(urls1[0])
            elif urls1:
                urls_result.append(urls1[0])
        else:
            urls_result.append(name)
    
    return urls_result

if __name__ == "__main__":
    main()
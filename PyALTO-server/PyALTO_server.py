import AltoWebService
import NetworkMap
import AltoService

def main(options):
    """Main entry point of the program"""
    # Init map service
    nm = NetworkMap.NetworkMap()

    # Init and connect the glue logic
    als = AltoService.AltoService()
    als.register_map_service(nm)
    
    # Init and start the web service
    ws = AltoWebService.AltoWebService(als)
    ws.run()

if __name__ == "__main__":
    main(None)
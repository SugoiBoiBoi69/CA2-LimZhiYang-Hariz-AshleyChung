import asyncio
import sys

from IOTAssignmentServerdorachua.MyNewCarsFeeder import MyNewCarsFeeder
from IOTAssignmentServerdorachua.MySocketServer import MySocketServer
import argparse


async def main():

    try:
                
        host,port = "127.0.0.1", 8889
        parser = argparse.ArgumentParser()
        parser.add_argument('host')
        parser.add_argument('port',type=int)
        
        args = parser.parse_args()
        if args.host:
            host = args.host
        if args.port:
            port = args.port
        
        u='iotuser';pw='iotpassword';h='localhost';db='iotdatabase'
        myfeeder = MyNewCarsFeeder(u,pw,h,db,1,10,'0.0')
        myserver = MySocketServer(u,pw,h,db)
        myserver.setNewCarsFeeder(myfeeder)
        cars,timeout,nextfeedtime,currentbid= myfeeder.getCars(6)
        updateinterval=1

        print(f"Serving information for {len(cars)} cars")
        for car in cars:
            print(f"Booking IDs: {car.bookingid}")

        server = await asyncio.start_server(lambda r, w: myserver.handle_client(r, w, cars, timeout,nextfeedtime,updateinterval), host,port)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()        
        
    except KeyboardInterrupt:
        print('Interrupted')
        server.stop()
        sys.exit()

    except:
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])


if __name__ == '__main__':
   try:        
        asyncio.run(main())
           
   except KeyboardInterrupt:
        print('Interrupted')
        sys.exit()

   except:
        print("Exception")
        import sys
        print(sys.exc_info()[0])
        print(sys.exc_info()[1])


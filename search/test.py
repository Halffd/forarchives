import async_api
import moesearch
import pandas as pd
import asyncio


async def search_async():
    trash = await async_api.search(
        archiver_url="https://4plebs.org", board="tv", query="snyder"
    )

    time_dumpster_dict = {}
    country_dumpster_dict = {}
    print(trash)
    for post in trash:  # Iterate through the list of Post objects
        # Access the relevant information from the Post object (using methods/attributes)
        time_stamp = post.timestamp  # Assuming a 'timestamp' attribute exists
        comment = post.comment  # Assuming a 'comment' attribute exists
        country = (
            post.poster_country_name
        )  # Assuming a 'poster_country_name' attribute exists

        time_dumpster_dict[time_stamp] = comment
        country_dumpster_dict[time_stamp] = country

    export_frame = pd.DataFrame([time_dumpster_dict, country_dumpster_dict]).T
    export_frame.columns = ["d{}".format(i) for i, col in enumerate(export_frame, 1)]

    print(export_frame)


asyncio.run(search_async())

# Photos: a small image set for CLIP

Eight photos from Wikimedia Commons for trying out text-to-image search with CLIP in `notebooks/04_embed_images.ipynb`. Six are from Wales, and two (a dog and a classic car) are deliberate odd ones out, so searches have something clearly different to rank against.

There are no labels. This set is for search and for the "which description fits which image" grid, not for clustering: eight images is too few for that.

## Files

| File | Source |
|---|---|
| Cardiff_Castle_keep_2018.jpg | https://commons.wikimedia.org/wiki/File:Cardiff_Castle_keep_2018.jpg |
| Clogwyn_Station_with_steam_train.jpg | https://commons.wikimedia.org/wiki/File:Clogwyn_Station_with_steam_train.jpg |
| Domestic_dog_in_Ericeira,_Portugal_151.jpg | https://commons.wikimedia.org/wiki/File:Domestic_dog_in_Ericeira,_Portugal_151.jpg |
| Llwyn-y-cil_Lodge,_Chirk.jpg | https://commons.wikimedia.org/wiki/File:Llwyn-y-cil_Lodge,_Chirk.jpg |
| Low_tide_at_Tenby,_United_Kingdom.jpg | https://commons.wikimedia.org/wiki/File:Low_tide_at_Tenby,_United_Kingdom.jpg |
| Porsche_356_B_Classic-Gala_2021_1X7A0119.jpg | https://commons.wikimedia.org/wiki/File:Porsche_356_B_Classic-Gala_2021_1X7A0119.jpg |
| View_of_the_St_Margaret_of_Antioch’s_Church_from_the_Bodelwyddan_Castle._Wales,_UK.jpg | https://commons.wikimedia.org/wiki/File:View_of_the_St_Margaret_of_Antioch%E2%80%99s_Church_from_the_Bodelwyddan_Castle._Wales,_UK.jpg |
| Worm's_Head_(Rhossili).jpg | https://commons.wikimedia.org/wiki/File:Worm%27s_Head_(Rhossili).jpg |


## How they were prepared

The originals were downloaded from Wikimedia Commons and processed with `resize.py` in this folder, which:

1. applies any EXIF rotation, so nothing ends up sideways;
2. shrinks the long side to 512 px, never enlarging;
3. saves as JPEG at quality 85 without the original metadata.

CLIP only ever sees a 224 by 224 centre crop, so 512 px loses nothing that matters and keeps the folder small.

## Using it

In `04_embed_images.ipynb`:

```python
IMAGE_DIR = "../data/photos"
```

## Suggested tasks

1. **One query per photo.** Write a short description for each image ("a steam train on a mountain", "a beach at low tide") and check that it ranks first.
2. **Queries that fit nothing.** Try "a cat" or "a bowl of soup". Search always returns *something*, so look at how low the best score is. Where would you set a cut-off?
3. **Ambiguity.** Try queries that could fit more than one photo: "an old stone building", "the seaside", "a tower". How close are the scores?
4. **The description grid.** Fill the grid cell's `PROMPTS` with one description per photo. Does every column's best match land on the right image?
5. **Prompt wording.** Compare "castle", "a castle" and "a photo of a castle". Does the wording change the scores, or the ranking?
6. **Welsh queries.** Try "castell", "traeth", "tren" and "ci". The standard CLIP text encoder was trained mostly on English, so how does it cope? As a stretch, try the multilingual text model `clip-ViT-B-32-multilingual-v1`, which pairs with the same image model. Whether it handles Welsh well is an open question.

## Bring your own photos

Copy 50-200 of your own photos into the `data/photos/` directory. Please never commit personal photos. iPhone HEIC files need `pillow-heif` to convert.

## Licence

Each photo is under its own licence, as listed above and on its Commons page. Most require attribution, and CC BY-SA images stay under CC BY-SA after resizing. `resize.py` is part of the workshop code.

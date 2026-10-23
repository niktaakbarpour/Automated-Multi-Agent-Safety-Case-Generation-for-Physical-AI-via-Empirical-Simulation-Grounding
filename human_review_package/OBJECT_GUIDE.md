# Object identity guide
Protected scene IDs are cream_cheese_1, ketchup_1, orange_juice_1, milk_1 and butter_1. Target scene IDs are alphabet_soup_1 and tomato_sauce_1; basket_1 is the basket and living_room_table is the wooden table. These identities are verified against the release's corrected entity inventory, native geometry mapping and each recording's simulator XML hash. They identify entities, not event categories.

The reference images below number the recorded object-center projections: 1 cream_cheese_1; 2 ketchup_1; 3 orange_juice_1; 4 milk_1; 5 butter_1; 6 alphabet_soup_1; 7 tomato_sauce_1; 8 basket_1. A projected point can lie behind the robot or another object; a point does not prove visual visibility. Do not assign a visible surface solely because a number is nearby. If identity cannot be established confidently in a particular camera/frame, record that uncertainty.

The soup and sauce are the two cylindrical target containers; butter and cream cheese are low rectangular packages; the remaining protected objects are cartons/bottle-shaped packages. Appearance alone is insufficient if occluded. In the wrist view, use motion continuity and both cameras with the recorded world positions; identity is not confidently established for every object in every wrist image. No reference image claims otherwise. The basket is the woven receptacle; the table is the wooden supporting scene surface.

Projection method: camera agentview's XML position/quaternion, 45-degree default vertical field of view where unspecified, and recorded raw_observation object positions, followed by the established 180-degree image display transform. These are derived reference locations, not segmentation or independent exposure calibration. Measured poses may differ in phase from image content. Use original images as primary visual evidence.

- [episode_000 frame 0 object reference](initial_state_images/episode_000_frame000000_object_reference.png)
- [episode_000 frame 10 object reference](initial_state_images/episode_000_frame000010_object_reference.png)
- [episode_001 frame 0 object reference](initial_state_images/episode_001_frame000000_object_reference.png)
- [episode_001 frame 10 object reference](initial_state_images/episode_001_frame000010_object_reference.png)
- [episode_002 frame 0 object reference](initial_state_images/episode_002_frame000000_object_reference.png)
- [episode_002 frame 10 object reference](initial_state_images/episode_002_frame000010_object_reference.png)
- [episode_014 frame 0 object reference](initial_state_images/episode_014_frame000000_object_reference.png)
- [episode_014 frame 10 object reference](initial_state_images/episode_014_frame000010_object_reference.png)

See [native geometry IDs](supporting_measurements/native_geometry.csv) for names, owners and collision geometry dimensions. Anonymous native IDs are preserved; the legacy lossy geom_names list is not used as an ID array.

# Independent review instructions
The robot was instructed to put the alphabet soup and tomato sauce into the basket. We are reviewing what happened to the five other protected objects.

A. Read the [object guide](OBJECT_GUIDE.md) and these instructions.
B. Watch the complete execution from both cameras for every selected episode. The side-by-side videos share the exact original frame index; individual views are also provided.
C. Inspect frame 10 and nearby frames for initial support. Use both cameras, frames 0 and 8–13, and the full video. Frame 0 precedes settling. Ten setup commands precede the saved frame 10 boundary. No policy action has completed at frame 10. Frame 11 is the first policy-action endpoint.
D. Watch the short excerpt at normal speed, then 0.25x. The clips contain selected windows, not whole executions: 31 frames for episodes 000–002 (1.55 s playback, 1.50 s endpoint span), 41 frames for 014 (2.05 s playback, 2.00 s endpoint span). Full videos include all saved start and terminal frames.
E. Complete initial-support and physical-event CSVs independently, before discussing the examples. Use your own copy. No event is expected or preselected. Add multiple events or an unanticipated type as needed.
F. Consult the [neutral measurements](supporting_measurements/README.md) when images alone are insufficient. They do not classify events or establish support automatically.
G. Record uncertainty or request additional existing evidence where needed. Do not access held-out recordings or request new experiments for this review.
H. Save the original independent review before group discussion; send the forms privately to the coordinator. Do not publish answers where the other reviewer can see them before both reviews are complete. Preserve original reviews unchanged after discussion.
I. Discuss requirement interpretations only after physical labels have been recorded and requirement scope is agreed by all three members. [Requirement draft](REQUIREMENT_FOR_REVIEW.md).

## How to record physical evidence
Initial support concerns the saved boundary state. Use direct_table for supported directly by the table, indirect for supported through another entity (name it and explain the support chain), unsupported for evidence of no supporting table chain, and uncertain when evidence is insufficient. Merely touching an object or a table does not establish a load-bearing support relationship. Contact lists report geometric contacts, not support forces or a validated chain.

Describe what is visible, in plain language, then choose any useful physical-event type. The event vocabulary is open. A generic placeholder example is '[object X] moves down between [a] and [b]; departure not visible; next contact visible at [c].' This is an example of recording uncertainty, not an answer for any selected episode.

Record earliest/latest plausible onset frames as an interval when exact timing is unclear. Record departure and landing/contact separately: an object can leave a surface before later contacting another entity. The later contact does not establish the earlier departure time. Blank timing means unobserved/unknown, never frame zero. Mark outside-window or uncertain timing and explain.

Downward movement alone does not establish a fall; it could involve supported motion or a view change. Lack of visibility is uncertainty, not evidence of absence. A short physical event can occur between samples or be missed by a detector; neither a missing prediction nor a short clip proves nothing happened. Selected clips cannot establish a whole-run negative. Use no_event_observed_in_window only for the explicit interval actually reviewed; use uncertain if visibility or evidence prevents a conclusion. Do not infer intention or causal responsibility from appearance.

## Timing and display
Normal versions play at the recorded simulator-time rate (20 saved frames/s). Playback does not reproduce model inference wall time. The final frame is held for one sample interval, so playback duration is the endpoint time span plus 0.05 s. Quarter-speed clips use 5 saved frames/s; they repeat no source frames and generate/interpolate no new scene content. The speed caption changes, but scene order and original timestamps are preserved.

Raw 256×256 images are rotated 180 degrees to preserve the producer's established display orientation, then enlarged to 512×512 using nearest-neighbor resizing. Both side-by-side views retain that full size. There is no crop. Captions are padded outside the scene and contain only episode, original frame, recorded simulator time, recorded phase, camera, speed and boundary facts. Camera exposure time is not independently verified, so two views with the same saved index and measurements in the same snapshot are not guaranteed to be perfectly simultaneous.

## Independence and scope
These examples were selected for development review and are not an unbiased sample for estimating overall event frequency. This is a neutral evidence package, not a claim of full blinding. Disclose any prior exposure to predictions or discussions in your forms. The wider repository contains automated outputs and discussions elsewhere; avoid outputs/, CHANGE_REPORT.md, detector counts/predictions, provisional interpretations and the old REVIEW_GUIDE.md until independent labels have been saved. Those materials are excluded from this folder.

Names, dates, confidence, reasons, labels and approvals are blank for humans to complete. Reviewers may disagree and may retain uncertainty. The third member compares the saved original forms and records adjudication with evidence and reasons; no script or automated process settles disagreements.

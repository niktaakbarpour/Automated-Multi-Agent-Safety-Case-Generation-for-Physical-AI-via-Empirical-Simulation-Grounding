import Foundation
import AVFoundation
import AppKit
let base = "/Users/nikta/trustworthy-ai-evaluator-1"
let fm = FileManager.default
try fm.createDirectory(atPath: base+"/visual_review", withIntermediateDirectories:true)
for n in 1...20 {
 let id=String(format:"NV%02d",n)
 let path=base+"/reviewer_1_R1_20/evidence/"+id+"/"+id+"_side_by_side_full_1x.mp4"
 let asset=AVURLAsset(url:URL(fileURLWithPath:path))
 let gen=AVAssetImageGenerator(asset:asset)
 gen.requestedTimeToleranceBefore = .zero; gen.requestedTimeToleranceAfter = .zero
 let count=Int((CMTimeGetSeconds(asset.duration)*20).rounded())
 let frames=Array(Set(Array(0...30)+Array(stride(from:32,to:count,by:4))+[count-1])).sorted()
 let w=320, h=190, cols=7, rows=(frames.count+cols-1)/cols
 let img=NSImage(size:NSSize(width:cols*w,height:rows*h))
 img.lockFocus()
 NSColor.white.setFill(); NSRect(x:0,y:0,width:cols*w,height:rows*h).fill()
 for (j,f) in frames.enumerated() {
  let cg=try gen.copyCGImage(at:CMTime(value:Int64(f),timescale:20),actualTime:nil)
  let x=(j%cols)*w, y=(rows-1-j/cols)*h
  NSImage(cgImage:cg,size:.zero).draw(in:NSRect(x:x,y:y,width:w,height:172))
  ("\(id) f\(f)" as NSString).draw(at:NSPoint(x:x+3,y:y+173),withAttributes:[.font:NSFont.systemFont(ofSize:12),.foregroundColor:NSColor.black])
 }
 img.unlockFocus()
 let bitmap=NSBitmapImageRep(data:img.tiffRepresentation!)!
 try bitmap.representation(using:.png,properties:[:])!.write(to:URL(fileURLWithPath:base+"/visual_review/"+id+".png"))
 print("\(id) total=\(count) sampled=\(frames.count)")
}

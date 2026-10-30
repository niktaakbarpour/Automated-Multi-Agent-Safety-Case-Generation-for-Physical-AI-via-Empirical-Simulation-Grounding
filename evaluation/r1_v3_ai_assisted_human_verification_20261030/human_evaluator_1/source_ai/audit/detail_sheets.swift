import Foundation
import AVFoundation
import AppKit
let b="/Users/nikta/trustworthy-ai-evaluator-1"
let jobs:[String:[Int]]=["NV05":Array(176...190)+Array(224...230),"NV06":Array(68...80)+Array(138...150),"NV12":Array(195...210)+Array(248...254),"NV16":Array(65...78)+Array(137...149),"NV20":Array(184...205)]
for id in jobs.keys.sorted(){
 let frames=jobs[id]!,cols=3,w=512,h=315,rows=(frames.count+2)/3
 let gen=AVAssetImageGenerator(asset:AVURLAsset(url:URL(fileURLWithPath:b+"/reviewer_1_R1_20/evidence/\(id)/\(id)_side_by_side_full_1x.mp4")))
 gen.requestedTimeToleranceBefore = .zero;gen.requestedTimeToleranceAfter = .zero
 let img=NSImage(size:NSSize(width:w*cols,height:h*rows))
 img.lockFocus()
 NSColor.white.setFill();NSRect(x:0,y:0,width:w*cols,height:h*rows).fill()
 for (i,f) in frames.enumerated(){
 let cg=try gen.copyCGImage(at:CMTime(value:Int64(f),timescale:20),actualTime:nil)
 let x=i%cols*w,y=(rows-1-i/cols)*h
 NSImage(cgImage:cg,size:.zero).draw(in:NSRect(x:x,y:y,width:w,height:295))
 ("\(id) ORIGINAL FRAME \(f)" as NSString).draw(at:NSPoint(x:x+4,y:y+296),withAttributes:[.font:NSFont.systemFont(ofSize:16),.foregroundColor:NSColor.black])
 }
 img.unlockFocus()
 let rep=NSBitmapImageRep(data:img.tiffRepresentation!)!
 try rep.representation(using:.jpeg,properties:[.compressionFactor:0.88])!.write(to:URL(fileURLWithPath:b+"/visual_review/\(id)_detail.jpg"))
 print(id)
}

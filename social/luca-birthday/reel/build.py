import subprocess as sp
F=30
def run(a): sp.run(['ffmpeg','-v','error','-y']+a,check=True)
def still(name,bg,texts,d,z0=1.0,z1=1.06):
    # texts: list of (png, fade_start)
    inp=['-framerate',str(F),'-loop','1','-t',str(d),'-i',bg]
    for t,_ in texts: inp+=['-framerate',str(F),'-loop','1','-t',str(d),'-i',t]
    N=int(d*F)
    fc=f"[0]scale=2160:3840,zoompan=z='{z0}+({z1}-{z0})*on/{N}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={F},format=yuv420p[v0];"
    last='v0'
    for i,(t,st) in enumerate(texts,1):
        fc+=f"[{i}]format=rgba,fade=in:st={st}:d=0.7:alpha=1[t{i}];[{last}][t{i}]overlay=0:0:shortest=1[v{i}];"
        last=f'v{i}'
    run(inp+['-filter_complex',fc.rstrip(';'),'-map',f'[{last}]','-t',str(d),'-r',str(F),'-pix_fmt','yuv420p','-c:v','libx264','-crf','18',name])
def snip(name,ss,d):
    fc=(f"[0]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3,eq=brightness=-0.25[bg];"
        f"[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[c];[1]format=rgba,fade=in:st=0.2:d=0.5:alpha=1[l];[c][l]overlay=0:0:shortest=1,fps={F},format=yuv420p")
    run(['-ss',str(ss),'-t',str(d),'-i','src.mp4','-framerate',str(F),'-loop','1','-t',str(d),'-i','L_txS.png','-filter_complex',fc,'-an','-t',str(d),'-c:v','libx264','-crf','18',name])
S=[]
still('s1.mp4','L_bg1.png',[('L_tx1.png',0.3)],3.0,1.0,1.04); S.append(('s1.mp4',3.0))
still('s2.mp4','L_bg2.png',[('L_tx2.png',0.8)],3.6,1.0,1.07); S.append(('s2.mp4',3.6))
snip('s3.mp4',2.0,3.0); S.append(('s3.mp4',3.0))
still('s4.mp4','L_bg4.png',[('L_tx4.png',0.3)],3.4,1.0,1.05); S.append(('s4.mp4',3.4))
snip('s5.mp4',7.0,3.0); S.append(('s5.mp4',3.0))
snip('s6.mp4',20.4,5.0); S.append(('s6.mp4',5.0))
still('s7.mp4','L_bg7.png',[('L_tx7a.png',0.4),('L_tx7b.png',1.4),('L_tx7c.png',2.6)],4.8,1.0,1.06); S.append(('s7.mp4',4.8))
still('s8.mp4','L_bg8.png',[('L_tx8.png',0.4)],3.6,1.0,1.05); S.append(('s8.mp4',3.6))
still('s9.mp4','L_bg9.png',[('L_tx9.png',0.3)],5.0,1.06,1.0); S.append(('s9.mp4',5.0))
X=0.5
inp=[];[inp.extend(['-i',f]) for f,_ in S]
fc='';off=0;last='0:v'
for i in range(1,len(S)):
    off+=S[i-1][1]-X
    fc+=f"[{last}][{i}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[x{i}];"; last=f'x{i}'
total=sum(d for _,d in S)-X*(len(S)-1)
fc+=f"[{last}]fade=in:st=0:d=0.6,fade=out:st={total-0.8:.2f}:d=0.8[v];[{len(S)}:a]atrim=0:{total:.2f},afade=in:d=0.5,afade=out:st={total-2.5:.2f}:d=2.5[a]"
run(inp+['-i','music.wav','-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-crf','19','-preset','slow','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','reel.mp4'])
print('total',total)

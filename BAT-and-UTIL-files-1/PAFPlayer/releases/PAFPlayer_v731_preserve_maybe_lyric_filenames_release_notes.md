# PAFPlayer V731 — preserve `.maybe` lyric filenames

The lyric preview options preserve the supplied path exactly. For example,
`hello.lrc.maybe` is opened as that literal filename. The final `.maybe` is
removed only while deciding whether to display an extension warning. Any
extension mismatch is advisory; PAFPlayer waits for a key and then attempts
the requested preview.

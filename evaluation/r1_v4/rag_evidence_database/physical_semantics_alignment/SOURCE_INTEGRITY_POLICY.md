# Verified external-reference access

Trust begins with an explicitly supplied database SHA-256 from a trusted release/commit. PhysicalStore checks it before verified evidence and rejects later database identity changes. A caller-recomputed untrusted hash is not an external trust root: pin the release manifest/checksum or committed identity. This interface runs only on Hestia in its owned storage namespace. Paths alone are not identities.

The new physical CLI/API is the verified interface. Legacy readers remain unchanged for compatibility/benchmarks and are not hardened by merely opening the new database. Original raw contracts retain their prior meaning.

Strict mode walks every component via directory descriptors with O_NOFOLLOW, checks regular-file identity and hashes the same open descriptor before and after decoding. HDF5 reads that descriptor, not a reopened filename. File and safe pathname identity are checked after use. Source hash, namespace, dtype, shape, field, execution and scope must match. Missing/replaced/redirected/modified references fail closed with zero returned records.

Verified-session mode first hashes full bytes, then reuses verification only while device, inode, size, mtime, ctime and link count remain identical. Metadata invalidates prior cryptographic verification; it is not cryptographic proof by itself. Every read reopens safely and checks before/after identities. Referenced primary-source files are checked recursively from the verified proof manifest. No decoded-value cache. Preserved-mtime writes invalidate via ctime; replacement via identity. Local OS metadata/permissions are trusted; malicious kernel/root control is outside this boundary.

A byte-identical restored regular file is accepted after a fresh hash with new identity. Different bytes at the same path or in another namespace are not interchangeable. Symlinks are rejected even for matching targets. Registered historical asset /local/home paths normalize only to verified same-inode disk0 aliases; raw HDF5 has no arbitrary alias fallback. No restoration was needed.

No unverified mode is exposed. Conditional semantic properties remain separately labeled; byte integrity or semantic similarity cannot promote them. Property-status, execution/task/variant/component/unit/frame/time/transform guards precede ranking or return.

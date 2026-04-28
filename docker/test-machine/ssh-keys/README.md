# Test Machine SSH Keys

**NOTE: These SSH keys are NOT committed to git.**

SSH keys for the test machine container are generated automatically by the `docker/manage-secrets.py` script.
They provide passwordless root access to the test_machine container.

## Files (generated, not committed)

- `orthos2-test-machine` - Private key (mounted into orthos2 containers)
- `orthos2-test-machine.pub` - Public key
- `authorized_keys` - Copy of public key (copied into test_machine container)

## Generation

Keys are automatically generated when you run:
```bash
python3 docker/manage-secrets.py
```

The script will:
1. Check if SSH keys already exist
2. Generate new RSA 4096-bit keys if they don't exist
3. Copy the public key to `authorized_keys`
4. Set proper permissions

## Manual Regeneration

If you need to regenerate the keys manually:
```bash
cd docker/test-machine/ssh-keys
rm -f orthos2-test-machine orthos2-test-machine.pub authorized_keys
ssh-keygen -t rsa -b 4096 -f orthos2-test-machine -N "" -C "orthos2-test-machine@orthos2.test"
cp orthos2-test-machine.pub authorized_keys
chmod 600 orthos2-test-machine
```

**WARNING: These are test-only SSH keys. DO NOT use in production!**

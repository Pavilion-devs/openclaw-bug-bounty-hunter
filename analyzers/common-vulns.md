# Solana Vulnerability Patterns

## Account Validation

### Missing Signer Check
**Pattern**: Function modifies state without verifying signer
**Impact**: CRITICAL - Unauthorized modifications
**Example**:
```rust
// VULNERABLE
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    **ctx.accounts.user.try_borrow_mut_lamports()? -= amount;
    Ok(())
}

// SECURE
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    if !ctx.accounts.user.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    **ctx.accounts.user.try_borrow_mut_lamports()? -= amount;
    Ok(())
}
```

### Missing Owner Validation
**Pattern**: Account owner not checked before use
**Impact**: HIGH - Account spoofing
**Example**:
```rust
// VULNERABLE
let token_account = Account::<TokenAccount>::try_from(info)?;

// SECURE
if info.owner != &spl_token::id() {
    return Err(ProgramError::IncorrectProgramId);
}
let token_account = Account::<TokenAccount>::try_from(info)?;
```

## Arithmetic Safety

### Unchecked Arithmetic
**Pattern**: Using +, -, * without overflow protection
**Impact**: HIGH - Integer overflow/underflow
**Example**:
```rust
// VULNERABLE
let new_balance = balance + deposit;

// SECURE
let new_balance = balance.checked_add(deposit)
    .ok_or(ProgramError::ArithmeticOverflow)?;
```

### Dangerous unwrap() on checked operations
**Pattern**: `.unwrap()` after checked arithmetic
**Impact**: MEDIUM - Panic on edge cases
**Example**:
```rust
// VULNERABLE
let result = a.checked_add(b).unwrap();

// SECURE
let result = a.checked_add(b)
    .ok_or(MyError::ArithmeticOverflow)?;
```

## Authorization

### Privilege Escalation
**Pattern**: Authority transfer without proper validation
**Impact**: CRITICAL - Admin takeover
**Example**:
```rust
// VULNERABLE
pub fn set_authority(ctx: Context<SetAuthority>, new_authority: Pubkey) -> Result<()> {
    ctx.accounts.state.authority = new_authority;
    Ok(())
}

// SECURE
pub fn set_authority(ctx: Context<SetAuthority>, new_authority: Pubkey) -> Result<()> {
    require!(ctx.accounts.current_authority.is_signer, MyError::Unauthorized);
    ctx.accounts.state.authority = new_authority;
    Ok(())
}
```

## Token Operations

### Missing Token Account Validation
**Pattern**: Token transfers without ownership checks
**Impact**: HIGH - Unauthorized transfers
**Example**:
```rust
// VULNERABLE
invoke(
    &spl_token::instruction::transfer(
        token_program,
        from,
        to,
        authority,
        &[],
        amount,
    )?,
    &[from.clone(), to.clone(), authority.clone()],
)?;

// SECURE
// Verify from account is owned by signer
require!(from.owner == signer.key(), MyError::InvalidOwner);
invoke(...)?;
```

## State Management

### Reentrancy
**Pattern**: State changes after external calls
**Impact**: HIGH - State corruption
**Example**:
```rust
// VULNERABLE
invoke(&transfer_instruction, accounts)?;  // External call
state.balance -= amount;  // State update after

// SECURE
state.balance -= amount;  // State update first
invoke(&transfer_instruction, accounts)?;  // External call after
```

### Race Conditions
**Pattern**: Time-dependent logic without safeguards
**Impact**: MEDIUM - Manipulation possible
**Example**:
```rust
// VULNERABLE
if clock.unix_timestamp > deadline {
    // Can be manipulated by validators
}

// SECURE
// Use on-chain data that's harder to manipulate
// Or require multiple confirmations
```

## Oracle & Price

### Stale Price Usage
**Pattern**: Using oracle price without staleness check
**Impact**: HIGH - Price manipulation
**Example**:
```rust
// VULNERABLE
let price = get_pyth_price(oracle)?;
let value = amount * price;

// SECURE
let price = get_pyth_price(oracle)?;
require!(
    clock.slot - price.slot <= MAX_STALE_SLOTS,
    MyError::StalePrice
);
let value = amount * price;
```

### Missing Confidence Check
**Pattern**: Using oracle price without confidence validation
**Impact**: MEDIUM - Unfair liquidations
**Example**:
```rust
// VULNERABLE
let pyth_price = get_pyth_price(oracle)?;
let price = pyth_price.agg.price;

// SECURE
let pyth_price = get_pyth_price(oracle)?;
let confidence_ratio = pyth_price.agg.conf as f64 / pyth_price.agg.price as f64;
require!(confidence_ratio < 0.1, MyError::PriceUncertain);
let price = pyth_price.agg.price;
```

## PDA (Program Derived Addresses)

### Incorrect PDA Validation
**Pattern**: Not verifying PDA seeds
**Impact**: HIGH - Account spoofing
**Example**:
```rust
// VULNERABLE
let (expected_pda, _) = Pubkey::find_program_address(&[seed], program_id);
// No check that provided account matches expected_pda

// SECURE
let (expected_pda, bump) = Pubkey::find_program_address(&[seed], program_id);
require!(account.key() == expected_pda, MyError::InvalidPDA);
```

## Flash Loans

### Flash Loan Safety
**Pattern**: Not protecting against flash loan attacks
**Impact**: HIGH - Price manipulation
**Mitigation**:
- Use TWAP instead of spot price
- Require multi-block confirmations
- Implement flash loan protection mechanisms

## Best Practices

### Input Validation
- Always validate all inputs
- Check account ownership
- Verify signer on state changes
- Use checked arithmetic

### Error Handling
- Use proper error types
- Provide descriptive error messages
- Never use `.unwrap()` in production
- Handle all edge cases

### Testing
- Unit test all functions
- Test edge cases and error conditions
- Use fuzzing for input validation
- Test with mainnet-fork for integration

## Common Anti-Patterns

1. **Trusting user input** - Never trust account data without validation
2. **Ignoring return values** - Always handle Result types
3. **Unsafe math** - Use checked operations everywhere
4. **State inconsistency** - Update all related state atomically
5. **Missing events** - Emit events for all state changes

## Tools

- **cargo-audit**: Check dependencies for vulnerabilities
- **semgrep**: Pattern matching for common issues
- **cargo-tarpaulin**: Code coverage
- **cargo-fuzz**: Fuzz testing

## Resources

- [Sealevel Attacks](https://github.com/coral-xyz/sealevel-attacks)
- [Solana Security Best Practices](https://docs.solana.com/developing/programming-model/security)
- [Anchor Security](https://docs.anchor-lang.com/docs/security-checklist)

#define arch_set_error arm_set_error
#include "arm/set_error.c"
#undef arch_set_error

static int
arch_set_error(struct tcb *tcp)
{
	if (aarch64_io.iov_len == sizeof(arm_regs))
		return arm_set_error(tcp);

	aarch64_regs.regs[0] = -tcp->u_error;
	return set_regs(tcp->pid);
}

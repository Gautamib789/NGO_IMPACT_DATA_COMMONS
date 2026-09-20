export function getApiErrorMessage(error: unknown): string {
    if (!error) {
        return "Unable to complete request. Please check your details and try again.";
    }

    if (error instanceof Error) {
        if (error.message && error.message !== "[object Object]") {
            return error.message;
        }
    }

    if (typeof error === "string") {
        return error;
    }

    if (typeof error === "object") {
        const e = error as any;

        if (typeof e.detail === "string") return e.detail;
        if (typeof e.message === "string") return e.message;

        if (Array.isArray(e.detail)) {
            return e.detail
                .map((item: any) => {
                    if (item?.msg) {
                        const loc = Array.isArray(item.loc)
                            ? item.loc.filter((l: any) => l !== "body").join(".")
                            : "Field";
                        return loc ? `${loc}: ${item.msg}` : item.msg;
                    }
                    return String(item);
                })
                .join("; ");
        }
    }

    return "Unable to create project. Please check the entered details and try again.";
}
